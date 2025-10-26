import calendar
import csv
import datetime
import logging
import os
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Sequence, List, Optional

from bot.db.models.models import User, WorkSchedule
from bot.entities.task import TaskCreate
from bot.exceptions.user_exceptions import InvalidCSVFile
from bot.services.ai_agent.tools import TaskTools
from bot.utils.unitofwork import UnitOfWork
from configreader import KYIV

SIMPLE_TASK_HEADERS = [
    "Telegram ID",
    "Ім'я + Посада",
    "Назва завдання",
    "Опис завдання",
    "Дата завдання",
    "Час початку (HH:MM)",
    "Час кінця (HH:MM)",
    "Категорія",
    "Фото",
    "Відео",
    "Документ",
]

REGULAR_TASK_HEADERS = [
    "Telegram ID",
    "Ім'я + Посада",
    "Назва завдання",
    "Опис завдання",
    "Номер Місяця завдання",
    "Рік завдання",
    "Час початку (HH:MM)",
    "Час кінця (HH:MM)",
    "Категорія",
    "Фото",
    "Відео",
    "Документ",
]


def get_row_data(user_id: int, full_name_and_position: str, is_regular: bool) -> list:
    if not is_regular:
        simple_task_row_data = [
            user_id,
            full_name_and_position,
            (datetime.datetime.now(KYIV) + datetime.timedelta(days=1)).strftime(
                "%Y-%m-%d"
            ),
            "",  # Task name (empty)
            "",  # Task description (empty)
            "",  # Start time (empty)
            "",  # End time (empty)
            "",  # Category (empty)\
            "-",  # Photo (empty)
            "-",  # Video (empty)
            "-",  # Document (empty)
        ]
        return simple_task_row_data
    else:
        task_month = datetime.datetime.now(KYIV).month
        current_day = datetime.datetime.now(KYIV).day
        task_year = datetime.datetime.now(KYIV).year
        max_days_in_month = calendar.monthrange(task_year, task_month)[-1]
        if current_day == max_days_in_month:
            task_month = task_month + 1
            next_year = datetime.datetime.now(KYIV).year + 1
            if task_month > 12:
                task_month = 1
                task_year = next_year

        regular_task_row_data = [
            user_id,
            full_name_and_position,
            "",  # Task name (empty)
            "",  # Task description (empty)
            task_month,  # Month
            task_year,
            "",  # Start time (empty)
            "",  # End time (empty)
            "",  # Category (empty)\
            "-",  # Photo (empty)
            "-",  # Video (empty)
            "-",  # Document (empty)
        ]
        return regular_task_row_data


def create_csv_tasks_template(users: Sequence[User], is_regular: bool) -> str:
    """
    Create a CSV file (Excel compatible) with all users from the database as a template for regular tasks.

    Args:
        users: List of User objects from the database
        is_regular: Whether the template is for regular tasks or for other tasks (e.g., for reminders)

    Returns:
        str: Path to the saved CSV file
    """
    # Create headers
    headers = REGULAR_TASK_HEADERS if is_regular else SIMPLE_TASK_HEADERS

    # Create a string buffer for CSV data
    output = StringIO()
    writer = csv.writer(output, delimiter=";")

    # Write headers
    writer.writerow(headers)

    # Write data for each user
    for user in users:
        # Prepare user information
        full_name = user.full_name or user.full_name_tg
        position_title = user.position.title if user.position else "Не вказано"
        user_info = f"{full_name} - {position_title}"

        # Create an empty row for the user as a template
        row_data = get_row_data(user.id, user_info, is_regular)
        # Write the row
        writer.writerow(row_data)

    # Convert to bytes
    csv_data = output.getvalue().encode(
        "utf-8-sig"
    )  # Use UTF-8 with BOM for Excel compatibility

    # Create directory for excel files if it doesn't exist
    excel_dir = Path("csv_files")
    excel_dir.mkdir(exist_ok=True)

    # Generate a unique filename
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    if is_regular:
        filename = f"regular_tasks_template_{current_date}.csv"
    else:
        filename = f"simple_tasks_template_{current_date}.csv"
    file_path = excel_dir / filename

    # Save the file to disk
    with open(file_path, "wb") as f:
        f.write(csv_data)

    return str(file_path.absolute())


async def parse_tasks_csv(
    file_path: str, uow: UnitOfWork, task_tools: TaskTools, is_regular: bool = True
) -> Dict[str, Any]:
    """
    Parse a CSV file with regular tasks and add them to the database.
    Creates an error report CSV file for problematic rows.

    The function validates each row in the CSV file and creates regular tasks for each user
    on their work days. If any errors are encountered during parsing, an error report CSV file
    is created with the problematic rows and detailed error descriptions.

    The error report CSV file includes:
    1. The original headers from the input file
    2. All problematic rows in their original form
    3. A blank row as a separator
    4. A section titled "Опис помилок:" (Error descriptions)
    5. For each problematic row, the row number and all error messages associated with it

    Args:
        file_path: Path to the CSV file
        uow: UnitOfWork object for database operations
        task_tools: TaskTools object for task-related operations

    Returns:
        Dict with statistics about the update:
        - tasks_created: Number of tasks created
        - errors: List of errors encountered
        - error_report_path: Path to the error report CSV file (if errors were found)
    """
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} not found")

    # Statistics to return
    stats = {
        "tasks_created": 0,
        "errors": [],
        "error_report_path": None,
        "created_tasks_ids": [],
    }

    # Dictionary to store problematic rows with their error messages
    # Key: row index, Value: list of error messages
    problematic_rows = {}

    # Read the CSV file
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")
        rows = list(reader)

    if len(rows) < 2:  # At least headers and one data row
        raise InvalidCSVFile(
            "Файл порожній. Використовуйте шаблон CSV для створення регулярних завдань"
        )

    # Parse headers
    headers = rows[0]
    headers_count_required = 11
    print(f"Parsed headers: {headers}")
    if len(headers) < headers_count_required:  # All required columns
        # raise InvalidCSVFile(
        #     "Заголовки написані не коректно. Перевірте формат файлу CSV."
        # )
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=",")
            rows = list(reader)
            if len(rows) < 2:  # At least headers and one data row
                raise InvalidCSVFile(
                    "Файл порожній. Використовуйте шаблон CSV для створення регулярних завдань"
                )
            headers = rows[0]
            if len(headers) < 11:  # All required columns
                raise InvalidCSVFile(
                    "Заголовки написані не коректно. Перевірте формат файлу CSV."
                )

    # Validate required headers
    expected_headers = SIMPLE_TASK_HEADERS if not is_regular else REGULAR_TASK_HEADERS

    for i, header in enumerate(expected_headers):
        if headers[i] != header:
            raise InvalidCSVFile(
                f"Заголовок '{header}' не знайдено або розміщений не правильно. Перевірте формат файлу CSV."
            )

    # Process data rows
    for row_index, row in enumerate(
        rows[1:], start=2
    ):  # Skip headers, start counting from 2 for error messages
        if len(row) < 7:
            error_msg = f"Рядок {row_index} має недостатньо інформації: {row}"
            stats["errors"].append(error_msg)
            if row_index not in problematic_rows:
                problematic_rows[row_index] = {"row": row, "errors": []}
            problematic_rows[row_index]["errors"].append(error_msg)
            continue
        month_str = None
        task_date_str = None
        # Extract data from row
        try:
            telegram_id = int(row[0])
            task_name = row[2].strip()
            task_description = row[3].strip()
            if is_regular:
                month_str = row[4].strip()
            else:
                task_date_str = row[4].strip()
            start_time_str = row[5].strip()
            end_time_str = row[6].strip()
            category_name = row[7].strip()
            # Optional fields (photo, video, document) can be empty
            photo = True if row[8].strip() == "+" else False
            video = True if row[9].strip() == "+" else False
            document = True if row[10].strip() == "+" else False

        except ValueError as e:
            error_msg = f"Помилка в рядку {row_index}: {e}"
            stats["errors"].append(error_msg)
            if row_index not in problematic_rows:
                problematic_rows[row_index] = {"row": row, "errors": []}
            problematic_rows[row_index]["errors"].append(error_msg)
            continue
        if not is_regular and not task_date_str:
            error_msg = f"Рядок {row_index}: Дата завдання не може бути порожньою"
            stats["errors"].append(error_msg)
            if row_index not in problematic_rows:
                problematic_rows[row_index] = {"row": row, "errors": []}
            problematic_rows[row_index]["errors"].append(error_msg)
            continue
        if is_regular and not month_str:
            error_msg = f"Рядок {row_index}: Місяць не може бути порожнім"
            stats["errors"].append(error_msg)
            if row_index not in problematic_rows:
                problematic_rows[row_index] = {"row": row, "errors": []}
            problematic_rows[row_index]["errors"].append(error_msg)
            continue
        # Validate required fields
        if not task_name:
            error_msg = f"Рядок {row_index}: Назва завдання не може бути порожньою"
            stats["errors"].append(error_msg)
            if row_index not in problematic_rows:
                problematic_rows[row_index] = {"row": row, "errors": []}
            problematic_rows[row_index]["errors"].append(error_msg)
            continue

        if not start_time_str or not end_time_str:
            error_msg = f"Рядок {row_index}: Час початку та кінця завдання не можуть бути порожніми"
            stats["errors"].append(error_msg)
            if row_index not in problematic_rows:
                problematic_rows[row_index] = {"row": row, "errors": []}
            problematic_rows[row_index]["errors"].append(error_msg)
            continue

        # Parse time values
        if not is_regular:
            try:
                task_date = datetime.datetime.strptime(task_date_str, "%Y-%m-%d").date()
                if task_date < datetime.date.today():
                    error_msg = f"Рядок {row_index}: Дата завдання ({task_date_str}) не може бути в минулому"
                    stats["errors"].append(error_msg)
                    if row_index not in problematic_rows:
                        problematic_rows[row_index] = {"row": row, "errors": []}
                    problematic_rows[row_index]["errors"].append(error_msg)
                    continue
            except ValueError:
                error_msg = f"Рядок {row_index}: Неправильний формат дати. Використовуйте формат YYYY-MM-DD"
                stats["errors"].append(error_msg)
                if row_index not in problematic_rows:
                    problematic_rows[row_index] = {"row": row, "errors": []}
                problematic_rows[row_index]["errors"].append(error_msg)
                continue
        try:
            start_time = (
                datetime.datetime.strptime(start_time_str, "%H:%M")
                .replace(tzinfo=KYIV)
                .time()
            )
            end_time = (
                datetime.datetime.strptime(end_time_str, "%H:%M")
                .replace(tzinfo=KYIV)
                .time()
            )
            if start_time >= end_time:
                error_msg = f"Рядок {row_index}: Час початку ({start_time_str}) не може бути пізніше або дорівнювати часу кінця ({end_time_str})"
                stats["errors"].append(error_msg)
                if row_index not in problematic_rows:
                    problematic_rows[row_index] = {"row": row, "errors": []}
                problematic_rows[row_index]["errors"].append(error_msg)
                continue
        except ValueError:
            error_msg = f"Рядок {row_index}: Неправильний формат часу. Використовуйте формат HH:MM"
            stats["errors"].append(error_msg)
            if row_index not in problematic_rows:
                problematic_rows[row_index] = {"row": row, "errors": []}
            problematic_rows[row_index]["errors"].append(error_msg)
            continue

        # Find user by Telegram ID
        user = await uow.users.find_one(id=telegram_id)
        if not user:
            error_msg = (
                f"Рядок {row_index}: Користувач з Telegram ID {telegram_id} не знайдено"
            )
            stats["errors"].append(error_msg)
            if row_index not in problematic_rows:
                problematic_rows[row_index] = {"row": row, "errors": []}
            problematic_rows[row_index]["errors"].append(error_msg)
            continue

        # Find or create category if provided
        category_id: Optional[int] = None
        if category_name:
            category = await uow.task_categories.find_one(name=category_name)
            if not category:
                # Create new category and get its id
                category_id = await uow.task_categories.add_one({"name": category_name})
            else:
                category_id = category.id
        if not is_regular:
            # Get all work schedules for the user in the future
            future_work_schedules: Sequence[
                WorkSchedule
            ] = await uow.work_schedules.get_all_work_schedule_in_user(
                user_id=user.id,
                from_date=task_date,
                to_date=task_date,
            )
        else:
            # Process regular task creation: month-based without specific date
            try:
                task_month = int(month_str)
                if task_month < 1 or task_month > 12:
                    raise ValueError
            except Exception:
                error_msg = f"Рядок {row_index}: Неправильний місяць '{month_str}'. Вкажіть число від 1 до 12"
                stats["errors"].append(error_msg)
                if row_index not in problematic_rows:
                    problematic_rows[row_index] = {"row": row, "errors": []}
                problematic_rows[row_index]["errors"].append(error_msg)
                continue

            await _create_regular_task(
                uow=uow,
                task_tools=task_tools,
                user=user,
                task_name=task_name,
                task_description=task_description,
                task_month=task_month,
                start_time=start_time,
                end_time=end_time,
                category_id=category_id,
                photo=photo,
                video=video,
                document=document,
                start_time_str=start_time_str,
                end_time_str=end_time_str,
                row_index=row_index,
                row=row,
                problematic_rows=problematic_rows,
                stats=stats,
            )
            # For regular tasks, continue to next row
            continue

        if not future_work_schedules:
            error_msg = f"Рядок {row_index}: Користувач з Telegram ID {telegram_id} не має робочих днів у майбутньому"
            stats["errors"].append(error_msg)
            if row_index not in problematic_rows:
                problematic_rows[row_index] = {"row": row, "errors": []}
            problematic_rows[row_index]["errors"].append(error_msg)
            continue

        # Create tasks for each work day
        for schedule in future_work_schedules:
            # Create datetime objects for start and end times
            schedule_date = schedule.date
            if schedule.start_time > start_time:
                error_msg = f"Рядок {row_index}: Час початку ({start_time_str}) не може бути раніше робочого часу ({schedule.start_time})"
                stats["errors"].append(error_msg)
                if row_index not in problematic_rows:
                    problematic_rows[row_index] = {"row": row, "errors": []}
                problematic_rows[row_index]["errors"].append(error_msg)
                break
            if schedule.end_time < end_time:
                error_msg = f"Рядок {row_index}: Час кінця ({end_time_str}) не може бути пізніше робочого часу ({schedule.end_time})"
                stats["errors"].append(error_msg)
                if row_index not in problematic_rows:
                    problematic_rows[row_index] = {"row": row, "errors": []}
                problematic_rows[row_index]["errors"].append(error_msg)
                break
            start_datetime = datetime.datetime.combine(
                schedule_date, start_time
            ).replace(tzinfo=KYIV)
            end_datetime = datetime.datetime.combine(schedule_date, end_time).replace(
                tzinfo=KYIV
            )

            # Check if task already exists for this user, date, and time
            existing_tasks = await uow.tasks.get_all_tasks(
                executor_id=user.id,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
            )

            existing_task_found = False
            for task in existing_tasks:
                if (
                    task.title == task_name
                    and task.description == task_description
                    and task.category_id == category_id
                    and task.start_datetime == start_datetime
                ):
                    existing_task_found = True
                    error_msg = f"Рядок {row_index}: Завдання вже існує для користувача {user.full_name} на {schedule_date} з часом початку {start_time_str} та кінця {end_time_str}"
                    stats["errors"].append(error_msg)
                    if row_index not in problematic_rows:
                        problematic_rows[row_index] = {"row": row, "errors": []}
                    problematic_rows[row_index]["errors"].append(error_msg)
                    break

            if existing_task_found:
                break  # Skip creating this task as it already exists

            # Create new task
            task_create = TaskCreate(
                creator_id=task_tools.user_id,  # User creates their own regular task
                executor_id=user.id,
                title=task_name,
                description=task_description,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                category_id=category_id,
                photo_required=photo,
                video_required=video,
                file_required=document,
            )

            # Add task to database
            new_task = task_create.model_dump(exclude_unset=True)
            task_id = await uow.tasks.add_one(new_task)
            await task_tools.create_notification_task_started(
                task_id,
                _defer_until=task_create.start_datetime,
            )
            await task_tools.create_notification_task_is_overdue(
                task_id,
                _defer_until=task_create.end_datetime,
            )
            await task_tools.create_notification_task_ending_soon(
                task_id,
                _defer_until=task_create.end_datetime - datetime.timedelta(minutes=30),
            )

            stats["tasks_created"] += 1
            stats["created_tasks_ids"].append(task_id)

        # Commit changes after processing each user
    await uow.commit()

    # Create error report CSV if there are any problematic rows
    if problematic_rows:
        logging.info(
            f"Found {len(problematic_rows)} problematic rows. Creating error report..."
        )

        # Create a string buffer for CSV data
        output = StringIO()
        writer = csv.writer(output, delimiter=";")

        # SECTION 1: Write headers (same as input file)
        writer.writerow(headers)

        # SECTION 2: Write problematic rows in order of row index
        # This allows the user to see all problematic rows together
        for row_index in sorted(problematic_rows.keys()):
            writer.writerow(problematic_rows[row_index]["row"])

        # Add a blank row as separator between data and error descriptions
        writer.writerow([])

        # SECTION 3: Add error descriptions section
        # This section provides detailed information about what's wrong with each row
        writer.writerow(["Опис помилок:"])
        for row_index in sorted(problematic_rows.keys()):
            # Write the row number
            writer.writerow([f"Рядок {row_index}:"])

            # Write each error message for this row with indentation for readability
            for error in problematic_rows[row_index]["errors"]:
                writer.writerow([f"  - {error}"])

            # Add empty row between different row error descriptions for better readability
            writer.writerow([])

        # Convert to bytes with UTF-8 encoding and BOM for Excel compatibility
        csv_data = output.getvalue().encode("utf-8-sig")

        # Create directory for error reports if it doesn't exist
        excel_dir = Path("csv_files")
        excel_dir.mkdir(exist_ok=True)

        # Generate a unique filename with timestamp to avoid overwriting previous reports
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = (
            f"simple_tasks_errors_{current_date}.csv"
            if not is_regular
            else f"regular_tasks_errors_{current_date}.csv"
        )
        file_path = excel_dir / filename

        # Save the file to disk
        with open(file_path, "wb") as f:
            f.write(csv_data)

        # Add error report path to stats for the caller to access
        stats["error_report_path"] = str(file_path.absolute())
        logging.info(f"Error report created at: {stats['error_report_path']}")

    logging.info(f"Regular tasks creation stats: {stats}")
    return stats


async def _create_regular_task(
    uow: UnitOfWork,
    task_tools: TaskTools,
    user: User,
    task_name: str,
    task_description: str,
    task_month: int,
    start_time: datetime.time,
    end_time: datetime.time,
    category_id: Optional[int],
    photo: bool,
    video: bool,
    document: bool,
    start_time_str: str,
    end_time_str: str,
    row_index: int,
    row: List[str],
    problematic_rows: Dict[int, Dict[str, Any]],
    stats: Dict[str, Any],
) -> None:
    """Create a regular (monthly) task for a user or record an error if duplicate exists.

    This writes results directly into stats and problematic_rows to minimize changes in the caller.
    """
    # Check duplicate regular task
    existing_regular = await uow.regular_tasks.find_one(
        executor_id=user.id,
        title=task_name,
        description=task_description,
        category_id=category_id,
        task_month=task_month,
        start_time=start_time,
        end_datetime=end_time,
    )
    if existing_regular:
        error_msg = (
            f"Рядок {row_index}: Регулярне завдання вже існує для користувача {user.full_name} "
            f"на місяць {task_month} з часом початку {start_time_str} та кінця {end_time_str}"
        )
        stats["errors"].append(error_msg)
        if row_index not in problematic_rows:
            problematic_rows[row_index] = {"row": row, "errors": []}
        problematic_rows[row_index]["errors"].append(error_msg)
        return

    # Create new regular task
    regular_task_data: Dict[str, Any] = {
        "creator_id": task_tools.user_id,
        "executor_id": user.id,
        "title": task_name,
        "description": task_description,
        "task_month": task_month,
        "start_time": start_time,
        "end_datetime": end_time,
        "category_id": category_id,
        "photo_required": photo,
        "video_required": video,
        "file_required": document,
    }
    regular_task_id = await uow.regular_tasks.add_one(regular_task_data)
    stats["tasks_created"] += 1
    stats["created_tasks_ids"].append(regular_task_id)
