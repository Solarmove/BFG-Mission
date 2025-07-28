from pydantic import BaseModel


class UserToolsData(BaseModel):
    all_tools: list
    analytics_tools: list


class WorkScheduleToolsData(BaseModel):
    all_tools: list
    analytics_tools: list


class CategoryToolsData(BaseModel):
    all_tools: list
    analytics_tools: list


class TaskToolsData(BaseModel):
    all_tools: list
    analytics_tools: list
