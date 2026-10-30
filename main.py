from typing import Annotated
from fastapi import FastAPI, HTTPException, Depends
import uvicorn
from pydantic import BaseModel
from sqlmodel import SQLModel, create_engine, Session, select
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

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@app.post("/tickets")
def create_ticket(ticket: CreateTicket, session: SessionDep):
    new_ticket = Ticket(
        title = ticket.title,
        description = ticket.description,
        )

    session.add(new_ticket)
    session.commit()
    session.refresh(new_ticket)

    return new_ticket

@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int, session: SessionDep):
    ticket = session.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return ticket

@app.get("/tickets")
def get_all_tickets(session: SessionDep):
    statement = select(Ticket)
    tickets = session.exec(statement).all()

    return tickets

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)