import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

from main import app, get_session

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def make_ticket(client: TestClient, title: str = "Printer offline"):
    response = client.post("/tickets", json={"title": title,
                                             "description": "Third floor printer shows an error"})

    assert response.status_code == 200
    return response.json()

def test_list_is_empty_at_start(client: TestClient):
    response = client.get("/tickets")

    assert response.status_code == 200
    assert response.json() == []

def test_create_ticket_defaults(client: TestClient):
    data = make_ticket(client)

    assert data["title"] == "Printer offline"
    assert data["status"] == "open"
    assert data["priority"] == "medium"
    assert data["id"] is not None

def test_missing_ticket(client: TestClient):
    response = client.get("/tickets/999")

    assert response.status_code == 404

def test_get_ticket(client: TestClient):
    data = make_ticket(client)
    response = client.get(f"/tickets/{data['id']}")
    fetched = response.json()

    assert response.status_code == 200
    assert fetched["id"] == data["id"]
    assert fetched["title"] == data["title"]

