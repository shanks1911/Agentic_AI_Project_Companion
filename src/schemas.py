from pydantic import BaseModel, Field
from typing import List, Literal

class KanbanTask(BaseModel):
    """Represents one task card on the board."""
    id: int = Field(..., description="Unique ID for the task, starting from 1.")
    title: str = Field(..., description="A short, clear title for the task.")
    description: str = Field(..., description="A brief description of what needs to be done.")
    status: Literal["To-Do"] = Field(default="To-Do")

class ProjectPlan(BaseModel):
    """The main structure for the project's Kanban plan."""
    project_title: str = Field(..., description="The official title of the project.")
    project_description: str = Field(..., description="A 1-2 sentence summary of the project.")
    tasks: List[KanbanTask] = Field(..., description="A list of 5-7 initial tasks for the 'To-Do' column.")
