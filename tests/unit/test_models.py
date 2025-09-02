# tests/test_database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Character, Film, Starship  # adjust import path if needed

# -------------------- Fixtures --------------------
@pytest.fixture(scope="module")
def engine():
    """Use an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def session(engine):
    # Clean schema before each test
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

# -------------------- Tests --------------------
def test_create_character(session):
    char = Character(name="Luke Skywalker", gender="male", birth_year="19BBY")
    session.add(char)
    session.commit()

    db_char = session.query(Character).filter_by(name="Luke Skywalker").first()
    assert db_char is not None
    assert db_char.gender == "male"
    assert db_char.birth_year == "19BBY"

def test_create_film(session):
    film = Film(title="A New Hope", director="George Lucas", release_date="1977-05-25")
    session.add(film)
    session.commit()

    db_film = session.query(Film).filter_by(title="A New Hope").first()
    assert db_film is not None
    assert db_film.director == "George Lucas"

def test_create_starship(session):
    ship = Starship(name="Millennium Falcon", model="YT-1300", manufacturer="Corellian Engineering Corp.")
    session.add(ship)
    session.commit()

    db_ship = session.query(Starship).filter_by(name="Millennium Falcon").first()
    assert db_ship is not None
    assert db_ship.model == "YT-1300"

def test_character_film_relationship(session):
    char = Character(name="Leia Organa")
    film = Film(title="Return of the Jedi")
    char.films.append(film)
    session.add(char)
    session.commit()

    db_char = session.query(Character).filter_by(name="Leia Organa").first()
    assert len(db_char.films) == 1
    assert db_char.films[0].title == "Return of the Jedi"

def test_character_starship_relationship(session):
    char = Character(name="Han Solo")
    ship = Starship(name="Millennium Falcon")
    char.starships.append(ship)
    session.add(char)
    session.commit()

    db_char = session.query(Character).filter_by(name="Han Solo").first()
    assert len(db_char.starships) == 1
    assert db_char.starships[0].name == "Millennium Falcon"

def test_film_starship_relationship(session):
    film = Film(title="Empire Strikes Back")
    ship = Starship(name="X-Wing")
    film.starships.append(ship)
    session.add(film)
    session.commit()

    db_film = session.query(Film).filter_by(title="Empire Strikes Back").first()
    assert len(db_film.starships) == 1
    assert db_film.starships[0].name == "X-Wing"
