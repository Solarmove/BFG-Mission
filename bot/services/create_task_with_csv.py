import csv
import datetime
import logging
import os
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Sequence

from bot.db.models.models import TaskCategory, User, WorkSchedule
from bot.entities.task import TaskCreate
from bot.exceptions.user_exceptions import InvalidCSVFile
from bot.services.ai_agent.tools import TaskTools
from bot.utils.unitofwork import UnitOfWork
from configreader import KYIV


def create_regular_tasks_template(users: Sequence[User]) -> str:
    """
    Create a CSV file (Excel compatible) with all users from the database as a template for regular tasks.

    Args:
        users: List of User objects from the database

    Returns:
        str: Path to the saved CSV file
    """
    # Create headers
    headers = [
        "Telegram ID",
        "Ім'я + Посада",
        "Дата завдання",
        "Назва завдання",
        "Опис завдання",
        "Час початку (HH:MM)",
        "Час кінця (HH:MM)",
        "Категорія",
        "Фото",
        "Відео",
        "Документ",
    ]

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
        row_data = [
            user.id,
            user_info,
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
    filename = f"regular_tasks_template_{current_date}.csv"
    file_path = excel_dir / filename

    # Save the file to disk
    with open(file_path, "wb") as f:
        f.write(csv_data)

    return str(file_path.absolute())


async def parse_regular_tasks_csv(
    file_path: str, uow: UnitOfWork, task_tools: TaskTools
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
    print(f"Parsed headers: {headers}")
    if len(headers) < 11:  # All required columns
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
    expected_headers = [
        "Telegram ID",
        "Ім'я + Посада",
        "Дата завдання",
        "Назва завдання",
        "Опис завдання",
        "Час початку (HH:MM)",
        "Час кінця (HH:MM)",
        "Категорія",
    ]

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

        # Extract data from row
        try:
            telegram_id = int(row[0])
            task_date_str = row[2].strip()
            task_name = row[3].strip()
            task_description = row[4].strip()
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
        if not task_date_str:
            error_msg = f"Рядок {row_index}: Дата завдання не може бути порожньою"
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
        category_id = None
        if category_name:
            category = await uow.task_categories.find_one(name=category_name)
            if not category:
                # Create new category
                category = TaskCategory(name=category_name)
                uow.session.add(category)
                # await uow.commit()
                category_id = category.id
            else:
                category_id = category.id

        # Get all work schedules for the user in the future
        future_work_schedules: Sequence[
            WorkSchedule
        ] = await uow.work_schedules.get_all_work_schedule_in_user(
            user_id=user.id,
            from_date=task_date,
            to_date=task_date,
        )

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
        filename = f"regular_tasks_errors_{current_date}.csv"
        file_path = excel_dir / filename

        # Save the file to disk
        with open(file_path, "wb") as f:
            f.write(csv_data)

        # Add error report path to stats for the caller to access
        stats["error_report_path"] = str(file_path.absolute())
        logging.info(f"Error report created at: {stats['error_report_path']}")

    logging.info(f"Regular tasks creation stats: {stats}")
    return stats
