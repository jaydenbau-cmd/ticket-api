from typing import Annotated
from fastapi import FastAPI, HTTPException, Depends
import uvicorn
from pydantic import BaseModel, field_validator
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

class UpdateTicket(BaseModel):
    status: Status | None = None
    priority: Priority | None = None

    @field_validator("status", "priority")
    @classmethod
    def validate_values(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value

sqlite_file_name = "tickets.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

allowed_next_status = {
    Status.open: [Status.in_progress],
    Status.in_progress: [Status.closed],
    Status.closed: [],
}

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
def get_all_tickets(session: SessionDep, status: Status | None = None, priority: Priority | None = None):

    statement = select(Ticket)
    if status is not None:
        statement = statement.where(Ticket.status == status)

    if priority is not None:
        statement = statement.where(Ticket.priority == priority)

    tickets = session.exec(statement).all()

    return tickets

@app.patch("/tickets/{ticket_id}")
def update_ticket(ticket_id: int, update: UpdateTicket, session: SessionDep):
    ticket = session.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    current_status = ticket.status
    update_data = update.model_dump(exclude_unset=True)

    if "status" in update_data:
        requested = update_data["status"]

        if not requested in allowed_next_status[current_status]:
            allowed = [s.value for s in allowed_next_status[current_status]]
            allowed_text = ", ".join(allowed) or "none"
            raise HTTPException(status_code=409, detail=f"Cannot move ticket from '{current_status.value}' to '{requested.value}'. Allowed: '{allowed_text}'")

    ticket.sqlmodel_update(update_data)
    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    return ticket

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)