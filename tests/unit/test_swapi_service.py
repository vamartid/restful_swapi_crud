# tests/test_swapi_service.py

import pytest
from unittest.mock import patch, Mock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.database import Base
from app.models import Character, Film, Starship
import app.services.swapi_service as swapi
from app.services import swapi_sync
import requests

# ---------------------- Fixtures ----------------------

@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database and session for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def mock_db():
    return MagicMock()

# ---------------------- fetch_from_swapi ----------------------

@patch("app.services.swapi_service.requests.get")
def test_fetch_from_swapi_success(mock_get):
	# Successful fetch
	mock_resp = Mock()
	mock_resp.json.return_value = {"results": [{"name": "Luke"}]}
	mock_resp.raise_for_status.return_value = None
	mock_get.return_value = mock_resp

	result = swapi.fetch_from_swapi("people")
	assert isinstance(result, list)
	assert result[0][0]["name"] == "Luke"

@patch("app.services.swapi_service.requests.get")
def test_fetch_from_swapi_retries(mock_get):
    # First 2 attempts fail with RequestException, third returns empty results
    mock_get.side_effect = [
        requests.exceptions.RequestException("Failed"),
        requests.exceptions.RequestException("Failed"),
        Mock(json=Mock(return_value={"results": []}), raise_for_status=Mock())
    ]

    result = swapi.fetch_from_swapi("people", retries=3, delay=0, fail_fast=False)
    assert result[0] == []


@patch("app.services.swapi_service.requests.get")
def test_fetch_from_swapi_failure_raises(mock_get):
    from fastapi import HTTPException
    mock_get.side_effect = requests.exceptions.RequestException("Failed")

    with pytest.raises(HTTPException) as exc_info:
        swapi.fetch_from_swapi("people", retries=2, delay=0, fail_fast=True)

    assert exc_info.value.status_code == 502
	
# ---------------------- store_objects ----------------------

def test_store_objects_adds_to_db(db_session):
    data_list = [{"name": "Luke", "gender": "male", "birth_year": "19BBY"}]
    swapi.store_objects(db_session, Character, data_list, "name")
    chars = db_session.query(Character).all()
    assert len(chars) == 1
    assert chars[0].name == "Luke"

def test_store_objects_skips_duplicates(db_session):
    data_list = [{"name": "Luke", "gender": "male", "birth_year": "19BBY"}]
    swapi.store_objects(db_session, Character, data_list, "name")
    # Store again
    swapi.store_objects(db_session, Character, data_list, "name")
    chars = db_session.query(Character).all()
    assert len(chars) == 1  # duplicate skipped

# ---------------------- store_characters / films / starships ----------------------

def test_store_characters(db_session):
    mock_data = [{"name": "Leia", "gender": "female", "birth_year": "19BBY"}]
    swapi.store_characters(db_session, mock_data)
    assert db_session.query(Character).filter_by(name="Leia").first() is not None

def test_store_films(db_session):
    mock_data = [{"title": "A New Hope", "director": "George Lucas", "release_date": "1977-05-25"}]
    swapi.store_films(db_session, mock_data)
    assert db_session.query(Film).filter_by(title="A New Hope").first() is not None

def test_store_starships(db_session):
    mock_data = [{"name": "X-Wing", "model": "T-65", "manufacturer": "Incom"}]
    swapi.store_starships(db_session, mock_data)
    assert db_session.query(Starship).filter_by(name="X-Wing").first() is not None

# ---------------------- fill_relationships ----------------------

def test_fill_relationships(db_session):
    char = Character(name="Luke", gender="male")
    film = Film(title="A New Hope", director="George Lucas")
    ship = Starship(name="X-Wing", model="T-65")
    db_session.add_all([char, film, ship])
    db_session.commit()

    swapi.fill_relationships(db_session)

    # relationships should be filled
    assert film in char.films
    assert ship in char.starships
    assert ship in film.starships

# ---------------------- sync_all ----------------------

def test_sync_all_calls_all_functions(mock_db):
    with patch("app.services.swapi_service.fetch_characters") as mock_fetch_characters, \
         patch("app.services.swapi_service.store_characters") as mock_store_characters, \
         patch("app.services.swapi_service.fetch_films") as mock_fetch_films, \
         patch("app.services.swapi_service.store_films") as mock_store_films, \
         patch("app.services.swapi_service.fetch_starships") as mock_fetch_starships, \
         patch("app.services.swapi_service.store_starships") as mock_store_starships, \
         patch("app.services.swapi_service.fill_relationships") as mock_fill_relationships:

        mock_fetch_characters.return_value = [{"name": "Luke"}]
        mock_fetch_films.return_value = [{"title": "A New Hope"}]
        mock_fetch_starships.return_value = [{"name": "X-Wing"}]

        swapi_sync.sync_all(mock_db)

        # Assert fetches
        mock_fetch_characters.assert_called_once()
        mock_fetch_films.assert_called_once()
        mock_fetch_starships.assert_called_once()

        # Assert stores
        mock_store_characters.assert_called_once_with(mock_db, [{"name": "Luke"}])
        mock_store_films.assert_called_once_with(mock_db, [{"title": "A New Hope"}])
        mock_store_starships.assert_called_once_with(mock_db, [{"name": "X-Wing"}])

        # Assert relationships filled
        mock_fill_relationships.assert_called_once_with(mock_db)
