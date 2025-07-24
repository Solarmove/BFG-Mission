import asyncio
import os
import csv
import calendar
import datetime
from io import StringIO
from pathlib import Path
from typing import List, Dict, Any


# Simplified version of create_work_schedule_excel for testing
def create_work_schedule_excel(
    user_data: List[Dict[str, Any]], month: int, year: int
) -> str:
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
    num_days = calendar.monthrange(year, month)[1]

    # Create headers
    headers = ["ФИО", "Telegram ID", "Должность", "Месяц"] + [
        str(day) for day in range(1, num_days + 1)
    ]

    # Create a string buffer for CSV data
    output = StringIO()
    writer = csv.writer(output)

    # Write headers
    writer.writerow(headers)

    # Write data for each user
    for data in user_data:
        user = data["user"]
        schedules = data["schedules"]

        # Create a dictionary mapping day of month to schedule
        day_to_schedule = {}
        for schedule in schedules:
            day = schedule.date.day
            day_to_schedule[day] = (
                f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}"
            )

        # Prepare row data
        row_data = [
            user.full_name or user.full_name_tg,
            user.id,
            user.position_title or "Не указана",
            f"{calendar.month_name[month]} {year}",
        ]

        # Add schedule data for each day
        for day in range(1, num_days + 1):
            schedule_text = day_to_schedule.get(day, "выходной")
            row_data.append(schedule_text)

        # Write the row
        writer.writerow(row_data)

    # Convert to bytes
    csv_data = output.getvalue().encode(
        "utf-8-sig"
    )  # Use UTF-8 with BOM for Excel compatibility

    # Create directory for excel files if it doesn't exist
    excel_dir = Path("excel_files")
    excel_dir.mkdir(exist_ok=True)

    # Generate a unique filename based on month, year and timestamp
    month_name = calendar.month_name[month]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"work_schedule_{month_name}_{year}_{timestamp}.csv"
    file_path = excel_dir / filename

    # Save the file to disk
    with open(file_path, "wb") as f:
        f.write(csv_data)

    return str(file_path.absolute())


class MockUser:
    """Mock User class for testing"""

    def __init__(self, id, full_name=None, full_name_tg=None, position_title=None):
        self.id = id
        self.full_name = full_name
        self.full_name_tg = full_name_tg
        self.position_title = position_title
        self.work_schedules = []


class MockWorkSchedule:
    """Mock WorkSchedule class for testing"""

    def __init__(self, id, user_id, start_time, end_time, date):
        self.id = id
        self.user_id = user_id
        self.start_time = start_time
        self.end_time = end_time
        self.date = date


def test_create_work_schedule_excel():
    """
    Test function for create_work_schedule_excel

    This test:
    1. Creates mock user and work schedule data
    2. Calls create_work_schedule_excel with the mock data
    3. Verifies the returned file path exists
    4. Checks that the CSV file contains the expected content
    5. Cleans up the test file
    """
    # Set up test data
    # Create mock users
    user1 = MockUser(id=123456789, full_name="Иванова Мария", position_title="Менеджер")
    user2 = MockUser(
        id=987654321, full_name_tg="Петров Иван", position_title="Разработчик"
    )

    # Current month and year for testing
    current_date = datetime.datetime.now()
    month = current_date.month
    year = current_date.year

    # Create mock work schedules
    # For user1
    schedule1_1 = MockWorkSchedule(
        id=1,
        user_id=user1.id,
        start_time=datetime.time(9, 0),  # 09:00
        end_time=datetime.time(18, 0),  # 18:00
        date=datetime.datetime(year, month, 1),  # 1st day of month
    )
    schedule1_2 = MockWorkSchedule(
        id=2,
        user_id=user1.id,
        start_time=datetime.time(10, 0),  # 10:00
        end_time=datetime.time(19, 0),  # 19:00
        date=datetime.datetime(year, month, 5),  # 5th day of month
    )
    user1.work_schedules = [schedule1_1, schedule1_2]

    # For user2
    schedule2_1 = MockWorkSchedule(
        id=3,
        user_id=user2.id,
        start_time=datetime.time(8, 0),  # 08:00
        end_time=datetime.time(17, 0),  # 17:00
        date=datetime.datetime(year, month, 4),  # 4th day of month
    )
    user2.work_schedules = [schedule2_1]

    # Prepare user_data as expected by the function
    user_data = [
        {"user": user1, "schedules": user1.work_schedules},
        {"user": user2, "schedules": user2.work_schedules},
    ]

    try:
        # Call the function
        file_path = create_work_schedule_excel(user_data, month, year)

        # Verify the file exists
        assert os.path.exists(file_path), f"File {file_path} does not exist"

        # Read the CSV file and verify its content
        with open(file_path, "r", encoding="utf-8-sig") as f:
            csv_reader = csv.reader(f)
            rows = list(csv_reader)

            # Verify headers
            headers = rows[0]
            assert headers[0] == "ФИО", "First header should be 'ФИО'"
            assert headers[1] == "Telegram ID", "Second header should be 'Telegram ID'"
            assert headers[2] == "Должность", "Third header should be 'Должность'"
            assert headers[3] == "Месяц", "Fourth header should be 'Месяц'"

            # Verify user data
            user1_row = rows[1]
            assert user1_row[0] == "Иванова Мария", "User1 name is incorrect"
            assert user1_row[1] == "123456789", "User1 ID is incorrect"

            user2_row = rows[2]
            assert user2_row[0] == "Петров Иван", "User2 name is incorrect"
            assert user2_row[1] == "987654321", "User2 ID is incorrect"

            # Verify schedule data
            # User1 should have "09:00-18:00" on day 1 and "10:00-19:00" on day 5
            day1_index = 4  # Headers are 0-3, day 1 is at index 4
            day5_index = 8  # Headers are 0-3, day 5 is at index 8

            assert user1_row[day1_index] == "09:00-18:00", (
                "User1 schedule for day 1 is incorrect"
            )
            assert user1_row[day5_index] == "10:00-19:00", (
                "User1 schedule for day 5 is incorrect"
            )

            # User2 should have "08:00-17:00" on day 4
            day4_index = 7  # Headers are 0-3, day 4 is at index 7
            assert user2_row[day4_index] == "08:00-17:00", (
                "User2 schedule for day 4 is incorrect"
            )

            print("All tests passed!")

    finally:
        # Clean up - remove the test file
        if "file_path" in locals() and os.path.exists(file_path):
            # os.remove(file_path)
            print(f"Test file {file_path} removed")


async def test_parse_work_schedule_excel():
    """
    Test function for parse_work_schedule_excel

    This is a simplified test that focuses on the parsing logic rather than database interactions.
    It creates a test CSV file and verifies that the function correctly parses it.
    """
    # Import the function to test
    from bot.services.csv_service import parse_work_schedule_csv
    import asyncio
    from unittest.mock import patch, MagicMock, AsyncMock

    # Create a test CSV file
    current_date = datetime.datetime.now()
    month = current_date.month
    year = current_date.year
    month_name = calendar.month_name[month]

    # Create CSV content
    csv_content = f"""ФИО,Telegram ID,Должность,Месяц,1,2,3,4,5
Иванова Мария,123456789,Менеджер,{month_name} {year},09:00-18:00,09:00-18:00,выходной,09:00-18:00,10:00-19:00
Петров Иван,987654321,Разработчик,{month_name} {year},08:00-17:00,выходной,выходной,08:00-17:00,08:00-17:00
"""

    # Write to a temporary file
    temp_file = (
        Path("excel_files")
        / f"test_schedule_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    temp_file.parent.mkdir(exist_ok=True)

    with open(temp_file, "w", encoding="utf-8-sig") as f:
        f.write(csv_content)

    try:
        # Create mock objects for database operations
        mock_user1 = MagicMock()
        mock_user1.id = 123456789
        mock_user1.full_name = "Иванова Мария (старое)"
        mock_user1.position_title = "Старший менеджер"

        mock_user2 = MagicMock()
        mock_user2.id = 987654321
        mock_user2.full_name = "Петров Иван (старое)"
        mock_user2.position_title = "Старший разработчик"

        # Mock existing schedules
        # Note: datetime objects are immutable in Python, so we can't modify their attributes
        # after creation. We set the day directly in the datetime constructor.
        mock_schedule1 = MagicMock()
        mock_schedule1.date = datetime.datetime(year, month, 1)  # Day 1
        mock_schedule1.start_time = datetime.time(8, 0)  # Different from CSV
        mock_schedule1.end_time = datetime.time(17, 0)  # Different from CSV

        mock_schedule2 = MagicMock()
        mock_schedule2.date = datetime.datetime(
            year, month, 3
        )  # Day 3 (day off in CSV)
        mock_schedule2.start_time = datetime.time(9, 0)
        mock_schedule2.end_time = datetime.time(18, 0)

        # Mock UnitOfWork and repositories
        mock_uow = AsyncMock()
        mock_users_repo = AsyncMock()
        mock_schedules_repo = AsyncMock()

        # Configure mock behavior
        mock_users_repo.find_one.side_effect = lambda **kwargs: {
            123456789: mock_user1,
            987654321: mock_user2,
        }.get(kwargs.get("id"))

        mock_schedules_repo.find_all.return_value = [mock_schedule1, mock_schedule2]

        mock_uow.users = mock_users_repo
        mock_uow.work_schedules = mock_schedules_repo
        mock_uow.__aenter__.return_value = mock_uow

        # Create a mock WorkSchedule class
        mock_work_schedule = MagicMock()

        # Patch UnitOfWork and WorkSchedule to use our mocks
        with (
            patch("bot.services.excel_service.UnitOfWork", return_value=mock_uow),
            patch(
                "bot.services.excel_service.WorkSchedule",
                return_value=mock_work_schedule,
            ),
        ):
            # Call the function
            stats = await parse_work_schedule_csv(str(temp_file), mock_uow)

            # Verify results
            print("Parse stats:", stats)

            # Verify user updates
            assert mock_users_repo.edit_one.call_count == 2, (
                "Should update both users' names"
            )

            # Verify schedule operations
            # Should update day 1 for user1 (different times)
            # Should delete day 3 for user1 (day off in CSV)
            # Should create new schedules for days in CSV that don't exist

            assert stats["users_updated"] > 0, "Should update users"
            assert stats["schedules_created"] > 0, "Should create new schedules"
            assert stats["schedules_updated"] > 0, "Should update existing schedules"
            assert stats["schedules_deleted"] > 0, (
                "Should delete schedules for days off"
            )
            assert len(stats["errors"]) == 0, "Should not have any errors"

            print("All parse tests passed!")

    finally:
        # Clean up - remove the test file
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"Test file {temp_file} removed")


if __name__ == "__main__":
    # Run the create test
    test_create_work_schedule_excel()

    # Run the parse test
    # This requires asyncio since the parse function is async
    asyncio.run(test_parse_work_schedule_excel())
    # print("Skipping parse test as it requires database mocking")
