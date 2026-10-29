from fastapi import FastAPI, HTTPException
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

@app.get("/tickets/{ticket_id}")
def list_tickets(ticket_id: int):
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket
    raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)