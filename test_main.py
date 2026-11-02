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

def test_list_is_not_empty_once_tickets_added(client: TestClient):
    ticket_1 = make_ticket(client)
    ticket_2 = make_ticket(client, title="No internet connection")

    response = client.get("/tickets")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["id"] == ticket_1["id"]
    assert response.json()[1]["id"] == ticket_2["id"]

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

def test_open_to_in_progress_allowed(client: TestClient):
    ticket = make_ticket(client)
    response = client.patch(f"/tickets/{ticket['id']}", json={"status": "in_progress"})

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"

def test_open_to_closed_rejected(client: TestClient):
    ticket = make_ticket(client)
    response = client.patch(f"/tickets/{ticket['id']}", json={"status": "closed"})
    unchanged = client.get(f"/tickets/{ticket['id']}").json()

    assert response.status_code == 409
    assert unchanged["status"] == "open"

def test_closed_ticket_cannot_be_reopened(client: TestClient):
    ticket = make_ticket(client)
    url = f"/tickets/{ticket['id']}"

    assert client.patch(url, json={"status": "in_progress"}).status_code == 200
    assert client.patch(url, json={"status": "closed"}).status_code == 200

    response = client.patch(url, json={"status": "open"})
    unchanged = client.get(f"/tickets/{ticket['id']}").json()

    assert response.status_code == 409
    assert unchanged["status"] == "closed"

def test_filter_by_status(client: TestClient):
    ticket_1 = make_ticket(client)
    make_ticket(client, title="No internet connection")

    assert client.patch(f"/tickets/{ticket_1['id']}", json={"status": "in_progress"}).status_code == 200
    response = client.get("/tickets", params={"status": "in_progress"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == ticket_1["id"]

def test_filter_by_priority(client: TestClient):
    ticket_1 = make_ticket(client)
    make_ticket(client, title="No internet connection")

    assert client.patch(f"/tickets/{ticket_1['id']}", json={"priority": "high"}).status_code == 200
    response = client.get("/tickets", params={"priority": "high"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == ticket_1["id"]

def test_filter_by_status_and_priority(client: TestClient):
    ticket_1 = make_ticket(client)
    ticket_2 = make_ticket(client, title="No internet connection")

    assert client.patch(f"/tickets/{ticket_1['id']}", json={"status": "in_progress",
                                                           "priority": "high"}).status_code == 200
    assert client.patch(f"/tickets/{ticket_2['id']}", json={"status": "in_progress",}).status_code == 200
    response = client.get("/tickets", params={"status": "in_progress",
                                              "priority": "high"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == ticket_1["id"]

def test_null_rejected(client: TestClient):
    ticket_1 = make_ticket(client)

    status_response = client.patch(f"/tickets/{ticket_1['id']}", json={"status": None})
    priority_response = client.patch(f"/tickets/{ticket_1['id']}", json={"priority": None})
    unchanged = client.get(f"/tickets/{ticket_1['id']}").json()

    assert status_response.status_code == 422
    assert priority_response.status_code == 422
    assert unchanged["status"] == "open"
    assert unchanged["priority"] == "medium"

def test_priority_only_update(client: TestClient):
    ticket_1 = make_ticket(client)

    assert client.patch(f"/tickets/{ticket_1['id']}", json={"priority": "high"}).status_code == 200
    response = client.get(f"/tickets/{ticket_1['id']}")

    assert response.status_code == 200
    assert response.json()["priority"] == "high"
    assert response.json()["status"] == "open"

def test_patch_on_ticket_that_doesnt_exist(client: TestClient):
    response = client.patch("/tickets/999", json={"status": "closed"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Ticket not found"

def test_create_ticket_with_no_description(client: TestClient):
    response = client.post("/tickets", json={"title": "Printer Offline"})

    assert response.status_code == 422

def test_update_with_no_input(client: TestClient):
    ticket = make_ticket(client)

    assert client.patch(f"/tickets/{ticket['id']}", json={}).status_code == 200
    response = client.get(f"/tickets/{ticket['id']}")

    assert response.status_code == 200
    assert response.json()["status"] == "open"
    assert response.json()["priority"] == "medium"

def test_same_status(client: TestClient):
    ticket = make_ticket(client)

    assert client.patch(f"/tickets/{ticket['id']}", json={"status": "open"}).status_code == 409

def test_invalid_values(client: TestClient):
    ticket = make_ticket(client)

    assert client.patch(f"/tickets/{ticket['id']}", json={"status": "banana"}).status_code == 422
    response = client.get(f"/tickets/{ticket['id']}")

    assert response.status_code == 200
    assert response.json()["status"] == "open"
