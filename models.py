from enum import Enum
from datetime import datetime, UTC
from sqlmodel import Field, SQLModel

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Status(str, Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"

class Ticket(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    priority: Priority = Field(default=Priority.medium)
    title : str
    description: str
    status: Status = Field(default=Status.open)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))