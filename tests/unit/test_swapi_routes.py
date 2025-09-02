# tests/test_swapi_routes.py

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.models import Character, Film, Starship
from app.routes import swapi_routes

# ---------------------- Setup FastAPI app ----------------------
app = FastAPI()
app.include_router(swapi_routes.router)

# Override get_db for testing with in-memory SQLite
@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,   # 🔑 ensures same in-memory DB is reused
        future=True,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

# ---------------------- Helper function ----------------------
def add_sample_data(db_session):
    char1 = Character(name="Luke", gender="male", birth_year="19BBY")
    char2 = Character(name="Leia", gender="female", birth_year="19BBY")
    film1 = Film(title="A New Hope", director="George Lucas", release_date="1977-05-25")
    film2 = Film(title="Empire Strikes Back", director="Irvin Kershner", release_date="1980-05-21")
    ship1 = Starship(name="X-Wing", model="T-65", manufacturer="Incom")
    ship2 = Starship(name="TIE Fighter", model="Twin Ion Engine", manufacturer="Sienar")
    db_session.add_all([char1, char2, film1, film2, ship1, ship2])
    db_session.commit()
    return char1, char2, film1, film2, ship1, ship2

# ---------------------- GET endpoints ----------------------
def test_get_characters(client, db_session):
    add_sample_data(db_session)
    response = client.get("/swapi/characters")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_films(client, db_session):
    add_sample_data(db_session)
    response = client.get("/swapi/films")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_starships(client, db_session):
    add_sample_data(db_session)
    response = client.get("/swapi/starships")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_skip_limit_validation(client, db_session):
    add_sample_data(db_session)
    
    resp = client.get("/swapi/characters?skip=10001")
    assert resp.status_code == 400

    resp = client.get("/swapi/characters?limit=0")
    assert resp.status_code == 422

    resp = client.get("/swapi/characters?limit=101")
    assert resp.status_code == 422

# ---------------------- Search endpoints ----------------------
def test_search_characters(client, db_session):
    add_sample_data(db_session)
    resp = client.get("/swapi/characters/search?name=Luke")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Luke"

def test_search_films(client, db_session):
    add_sample_data(db_session)
    resp = client.get("/swapi/films/search?title=Hope")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert "Hope" in data[0]["title"]

def test_search_starships(client, db_session):
    add_sample_data(db_session)
    resp = client.get("/swapi/starships/search?name=X-Wing")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "X-Wing"

# ---------------------- Sync endpoints ----------------------
@patch("app.services.swapi_service.fetch_characters")
@patch("app.services.swapi_service.store_characters")
def test_sync_characters(mock_store, mock_fetch, client, db_session):
    mock_fetch.return_value = [{"name": "Luke"}]
    response = client.post("/swapi/sync/characters")
    assert response.status_code == 200
    assert "characters synced successfully" in response.json()["message"]

@patch("app.services.swapi_service.fetch_films")
@patch("app.services.swapi_service.store_films")
def test_sync_films(mock_store, mock_fetch, client):
    mock_fetch.return_value = [{"title": "A New Hope"}]
    response = client.post("/swapi/sync/films")
    assert response.status_code == 200
    assert "films synced successfully" in response.json()["message"]

@patch("app.services.swapi_service.fetch_starships")
@patch("app.services.swapi_service.store_starships")
def test_sync_starships(mock_store, mock_fetch, client):
    mock_fetch.return_value = [{"name": "X-Wing"}]
    response = client.post("/swapi/sync/starships")
    assert response.status_code == 200
    assert "starships synced successfully" in response.json()["message"]

# ---------------------- sync_all orchestration ----------------------
@patch("app.services.swapi_service.fetch_characters")
@patch("app.services.swapi_service.store_characters")
@patch("app.services.swapi_service.fetch_films")
@patch("app.services.swapi_service.store_films")
@patch("app.services.swapi_service.fetch_starships")
@patch("app.services.swapi_service.store_starships")
@patch("app.services.swapi_service.fill_relationships")
def test_sync_all_endpoint(mock_fill, mock_store_ship, mock_fetch_ship,
                           mock_store_film, mock_fetch_film,
                           mock_store_char, mock_fetch_char, client):
    mock_fetch_char.return_value = [{"name": "Luke"}]
    mock_fetch_film.return_value = [{"title": "A New Hope"}]
    mock_fetch_ship.return_value = [{"name": "X-Wing"}]

    response = client.post("/swapi/sync/all")
    assert response.status_code == 200
    assert "All SWAPI data synced successfully" in response.json()["message"]

# ---------------------- safe_route exception handling ----------------------
def test_safe_route_exception(client, db_session):
    # Patch a route function to raise exception
    with patch("app.services.swapi_service.fetch_characters", side_effect=Exception("fail")):
        resp = client.post("/swapi/sync/characters")
        assert resp.status_code == 500
        assert "Internal error" in resp.json()["detail"]
