from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from enum import Enum

app = FastAPI()

tickets = []

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class CreateTicket(BaseModel):
    title: str
    description: str
    priority: Priority = Priority.medium

@app.post("/ticket")
def create_ticket(ticket: CreateTicket):
    new_ticket = {
        "id": len(tickets) + 1,
        "priority": ticket.priority,
        "title": ticket.title,
        "description": ticket.description,
        "status": "open"
    }
    tickets.append(new_ticket)
    return new_ticket

@app.get("/tickets")
def list_tickets():
    return tickets

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)