import calendar
import csv
import datetime
import locale
import logging
import os
import re
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List

from bot.db.models.models import User, WorkSchedule
from bot.exceptions.user_exceptions import InvalidCSVFile
from bot.utils.unitofwork import UnitOfWork

locale.setlocale(locale.LC_TIME, "C")  # Английская локаль


def create_work_schedule_csv(user_data: List[User], month: int, year: int) -> str:
    """
    Create a CSV file (Excel compatible) with work schedules for users and save it to disk.

    Args:
        user_data: List of dictionaries containing user information and their work schedules
                  Each dictionary should have:
                  - 'user': User object
                  - 'schedules': List of WorkSchedule objects for the specified month
        month: Month number (1-12)
        year: Year (e.g., 2024)

    Returns:
        str: Path to the saved CSV file
    """
    # Get the number of days in the month
    # pprint(user_data)
    num_days = calendar.monthrange(year, month)[1]

    # Create headers
    headers = ["ПІБ", "Telegram ID", "Посада", "Місяць"] + [
        str(day) for day in range(1, num_days + 1)
    ]

    # Create a string buffer for CSV data
    output = StringIO()
    writer = csv.writer(output, delimiter=";")

    # Write headers
    writer.writerow(headers)

    # Write data for each user
    for data in user_data:
        schedules = data.work_schedules

        # Create a dictionary mapping day of month to schedule
        day_to_schedule = {}

        for schedule in schedules:
            day = schedule.date.day
            day_to_schedule[day] = (
                f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}"
            )
        # Prepare row data
        row_data = [
            data.full_name or data.full_name_tg,
            data.id,
            data.position.title or "Не вказано",
            f"{calendar.month_name[month]} {year}",
        ]

        # Add schedule data for each day
        for day in range(1, num_days + 1):
            schedule_text = day_to_schedule.get(day, "вихідний")
            row_data.append(schedule_text)

        # Write the row
        writer.writerow(row_data)

    # Convert to bytes
    csv_data = output.getvalue().encode(
        "utf-8-sig"
    )  # Use UTF-8 with BOM for Excel compatibility

    # Create directory for excel files if it doesn't exist
    excel_dir = Path("csv_files")
    excel_dir.mkdir(exist_ok=True)

    # Generate a unique filename based on month, year and timestamp
    filename = f"work_schedule_{month}_{year}.csv"
    file_path = excel_dir / filename

    # Save the file to disk
    with open(file_path, "wb") as f:
        f.write(csv_data)

    return str(file_path.absolute())


async def parse_work_schedule_csv(file_path: str, uow: UnitOfWork) -> Dict[str, Any]:
    """
    Parse a CSV file with work schedules and update the database.

    Args:
        file_path: Path to the CSV file
        uow: UnitOfWork object for database operations

    Returns:
        Dict with statistics about the update:
        - users_updated: Number of users updated
        - schedules_created: Number of schedules created
        - schedules_updated: Number of schedules updated
        - schedules_deleted: Number of schedules deleted
        - errors: List of errors encountered
    """
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} not found")

    # Statistics to return
    stats = {
        "users_updated": 0,
        "schedules_created": 0,
        "schedules_updated": 0,
        "schedules_deleted": 0,
        "errors": [],
    }
    rows: list[list[str]] | None = None

    headers: list[str] = []
    encodings_to_try = [
        "utf-8-sig",
        "utf-8",
        "cp1251",
        "windows-1251",
        "cp1252",
        "latin1",
    ]
    delimiters_to_try = [";", ","]

    for enc in encodings_to_try:
        for delim in delimiters_to_try:
            try:
                with open(file_path, "r", encoding=enc, newline="") as f:
                    reader = csv.reader(f, delimiter=delim)
                    trial_rows = list(reader)
                    if trial_rows:  # At least headers exist
                        rows = trial_rows
                        temp_headers = rows[0]
                        logging.info(temp_headers)
                        if (
                            temp_headers[0] != "ПІБ"
                            or temp_headers[1] != "Telegram ID"
                            or temp_headers[2] != "Посада"
                            or temp_headers[3] != "Місяць"
                        ):
                            logging.info(
                                f"Headers do not match with encoding {enc} and delimiter {delim}. Trying next."
                            )
                            continue

                        headers = temp_headers
                        break
            except UnicodeDecodeError:
                # Try next encoding
                continue
        if rows is not None:
            break

    if rows is None:
        raise InvalidCSVFile(
            "Не вдалося прочитати CSV файл. Будь ласка, переконайтесь, що файл збережено в UTF-8 або Windows-1251."
        )

    if len(rows) < 2:  # At least headers and one data row
        raise InvalidCSVFile(
            "Файл порожній. Використовуйте шаблон CSV для створення регулярних завдань"
        )
    if headers is None or len(headers) < 5:
        raise InvalidCSVFile(
            "Недостатньо стовпців у файлі CSV. Використовуйте шаблон CSV для створення регулярних завдань"
        )

    # Extract days from headers (starting from index 4)
    days = []
    for i in range(4, len(headers)):
        try:
            day = int(headers[i])
            days.append(day)
        except ValueError:
            stats["errors"].append(f"Не правильний формат дати: {headers[i]}")

    # Parse month and year from the first data row
    month_year = rows[1][3]  # e.g., "July 2025"
    month_name, year_str = month_year.rsplit(" ", 1)

    try:
        year = int(year_str)
        # Convert month name to month number
        month_names = list(calendar.month_name)
        month = month_names.index(month_name)
        if month == 0:  # month_name not found
            raise ValueError(f"Неправильна назва місяця: {month_name}")
    except (ValueError, IndexError):
        raise InvalidCSVFile(f"Неправильний формат року: {month_year}")

    # Process data rows

    for row in rows[1:]:  # Skip headers
        if len(row) < 3:
            stats["errors"].append(f"Рядок має недостатньо інформації: {row}")
            continue

        # Extract user data
        full_name = row[0]
        try:
            telegram_id = int(row[1])
        except ValueError:
            stats["errors"].append(f"Некоректний Телеграм ID {row[1]}. Рядок {row}")
            continue

        # Find user by Telegram ID
        user = await uow.users.find_one(id=telegram_id)
        if not user:
            stats["errors"].append(
                f"Користувач з Телеграм ID {telegram_id} не знайдено. Рядок {row}"
            )
            continue

        # Update user's full_name if it's different
        if user.full_name != full_name:
            await uow.users.edit_one(user.id, {"full_name": full_name})
            stats["users_updated"] += 1

        # Get existing schedules for this user in the specified month
        start_date = datetime.datetime(year, month, 1)
        if month == 12:
            end_date = datetime.datetime(year + 1, 1, 1)
        else:
            end_date = datetime.datetime(year, month + 1, 1)

        existing_schedules = (
            await uow.work_schedules.get_all_work_schedules_for_date_to_date(
                date_from=start_date, date_to=end_date, user_id=user.id
            )
        )
        existing_schedules = [s for s in existing_schedules]

        # Create a dictionary of existing schedules by day
        existing_by_day = {s.date.day: s for s in existing_schedules}

        # Track days that are processed
        processed_days = set()
        logging.info(f"Processed days: {days}")
        logging.info(f"Existing days: {existing_by_day}")
        # Process each day's schedule
        for i, day in enumerate(days):
            if i + 4 >= len(row):  # Skip if row doesn't have data for this day
                logging.info(f"Row {row} does not have data for day {day}. Skipping.")
                continue

            schedule_text = row[i + 4].strip()
            processed_days.add(day)

            # Skip if it's a day off
            if schedule_text.lower() == "вихідний":
                if day in existing_by_day:
                    # Delete existing schedule for this day
                    logging.info(f"Deleting schedule for day {day} for user {user.id}")
                    existing_scheduler_model = existing_by_day[day]
                    await uow.work_schedules.delete_one(existing_scheduler_model.id)
                    await uow.commit()
                    stats["schedules_deleted"] += 1
                continue

            # Parse time range (e.g., "09:00-18:00")
            time_match = re.match(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})", schedule_text)
            if not time_match:
                stats["errors"].append(
                    f"Не правильний формат дати для дня {day}: {schedule_text}. Рядок {row}"
                )
                continue

            # Extract hours and minutes
            start_hour, start_minute, end_hour, end_minute = map(
                int, time_match.groups()
            )

            # Create datetime objects
            start_time = datetime.time(start_hour, start_minute)
            end_time = datetime.time(end_hour, end_minute)
            date = datetime.datetime(year, month, day)

            # Check if schedule already exists for this day
            if day in existing_by_day:
                existing = existing_by_day[day]
                # Update if different
                if existing.start_time != start_time or existing.end_time != end_time:
                    # existing.start_time = start_time
                    # existing.end_time = end_time
                    await uow.work_schedules.edit_one(
                        id=existing.id,
                        data={
                            "start_time": start_time,
                            "end_time": end_time,
                        },
                    )
                    stats["schedules_updated"] += 1
            else:
                # Create new schedule
                new_schedule = WorkSchedule(
                    user_id=user.id, start_time=start_time, end_time=end_time, date=date
                )
                uow.session.add(new_schedule)
                stats["schedules_created"] += 1

        # Delete schedules for days not in the CSV
        for day, schedule in existing_by_day.items():
            if day not in processed_days:
                await uow.work_schedules.delete_one(schedule.id)
                stats["schedules_deleted"] += 1

        # Commit all changes
        await uow.commit()
    logging.info(f"Finished processing CSV file {file_path}")
    logging.info(f"Statistics: {stats}")

    return stats
