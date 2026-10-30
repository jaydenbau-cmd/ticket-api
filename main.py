from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from sqlmodel import SQLModel, create_engine, Session
from contextlib import asynccontextmanager
from models import Ticket, Priority, Status

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(lifespan=lifespan)

class CreateTicket(BaseModel):
    title: str
    description: str

sqlite_file_name = "tickets.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

@app.post("/ticket")
def create_ticket(ticket: CreateTicket):
    new_ticket = Ticket(
        title = ticket.title,
        description = ticket.description,
        )

    with Session(engine) as session:
        session.add(new_ticket)
        session.commit()

    return new_ticket

@app.get("/tickets/{ticket_id}")
def list_tickets(ticket_id: int):
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket
    raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)