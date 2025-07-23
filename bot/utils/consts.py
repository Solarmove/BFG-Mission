from typing import Literal, TypeAlias

POSITION_TITLES: TypeAlias = Literal[
    "Директор",
    "CEO",
    "Асистент СЕО",
    "Керуючий",
    "HR",
    "Головний бухгалтер",
    "Бухгалтер",
    "Менеджер з продажу",
    "Менеджер по флористам",
    "Логіст",
    "Працівник складу",
    "Флорист",
]

positions_map: dict[POSITION_TITLES, int] = {
    "Директор": 1,
    "CEO": 2,
    "Асистент СЕО": 2,
    "Керуючий": 3,
    "HR": 3,
    "Головний бухгалтер": 3,
    "Бухгалтер": 3,
    "Менеджер з продажу": 4,
    "Менеджер по флористам": 4,
    "Логіст": 4,
    "Працівник складу": 4,
    "Флорист": 4,
}


def get_positions_titles(hierarchy_level: int):
    positions_map = {
        1: ["Директор"],
        2: ["CEO", "Асистент СЕО"],
        3: ["Керуючий", "HR", "Головний бухгалтер", "Бухгалтер"],
        4: [
            "Менеджер з продажу",
            "Менеджер по флористам",
            "Логіст",
            "Працівник складу",
            "Флорист",
        ],
    }
    if hierarchy_level not in positions_map:
        raise ValueError("Invalid hierarchy level provided.")
    return positions_map[hierarchy_level]