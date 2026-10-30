from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from enum import Enum
from sqlmodel import Field, SQLModel, create_engine
from datetime import datetime, UTC

app = FastAPI()

tickets = []

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Ticket(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    priority: Priority = Field(default=Priority.medium)
    title : str
    description: str
    status: str = Field(default="open")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class CreateTicket(BaseModel):
    title: str
    description: str

sqlite_file_name = "tickets.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

SQLModel.metadata.create_all(engine)

@app.post("/ticket")
def create_ticket(ticket: CreateTicket):
    new_ticket = Ticket(
        title = ticket.title,
        description = ticket.description,
        )

    return new_ticket

@app.get("/tickets/{ticket_id}")
def list_tickets(ticket_id: int):
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket
    raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)