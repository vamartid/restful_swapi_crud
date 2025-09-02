from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from app.models import Character, Film, Starship
import logging
from app.db_exceptions import handle_db_exception
import requests

# -------------------- BASE --------------------
SWAPI_BASE = "https://swapi.info/api"
"""
Base URL for SWAPI endpoints.
"""

# -------------------- Helpers --------------------
def fetch_from_swapi(endpoint: str, retries: int = 3, delay: int = 2, fail_fast: bool = True):
    """
    Fetch data from SWAPI with retries and error handling.

    Args:
        endpoint (str): SWAPI endpoint, e.g., "people", "films", "starships"
        retries (int): Number of retry attempts
        delay (int): Delay between retries in seconds
        fail_fast (bool): If True, raises HTTPException on failure (for FastAPI routes)
                          If False, returns empty list (for scripts)

    Returns:
        list: List of SWAPI items

    Raises:
        HTTPException: If fetching fails and fail_fast is True
    """
    import time
    import json
    from fastapi import HTTPException

    url = f"{SWAPI_BASE}/{endpoint}"
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            # SWAPI.info returns dict of items, not paginated 'results'
            if isinstance(data, dict):
                return list(data.values())
            return data
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            logging.warning(f"[Attempt {attempt}/{retries}] Error fetching {endpoint}: {e}")
            if attempt == retries:
                logging.error(f"Failed to fetch {endpoint} after {retries} attempts")
                if fail_fast:
                    raise HTTPException(status_code=502, detail=f"Failed to fetch {endpoint} from SWAPI")
                else:
                    return []
            time.sleep(delay)

def store_objects(db: Session, model_class, data_list, unique_field):
    """
    Store a list of objects into the database with uniqueness check.

    Args:
        db (Session): SQLAlchemy database session
        model_class: SQLAlchemy model class to store
        data_list (list): List of dicts containing object data
        unique_field (str): Field to check uniqueness

    Returns:
        None

    Raises:
        Exception: If database commit fails
    """
    added_count = 0
    try:
        for data in data_list:
            if not db.query(model_class).filter(getattr(model_class, unique_field) == data[unique_field]).first():
                obj = model_class(**{k: v for k, v in data.items() if hasattr(model_class, k)})
                db.add(obj)
                added_count += 1
        db.commit()
        logging.info(f"Stored {added_count}/{len(data_list)} {model_class.__name__}")
    except Exception as e:
        db.rollback()
        handle_db_exception(e, context=f"storing {model_class.__name__}")
        raise

# -------------------- Characters --------------------
def fetch_characters():
    """
    Fetch characters from SWAPI.

    Returns:
        list: List of character dicts
    """
    return fetch_from_swapi("people")

def store_characters(db: Session, characters_data):
    """
    Store characters into the database.

    Args:
        db (Session): Database session
        characters_data (list): List of character dicts

    Returns:
        None
    """
    processed = []
    for c in characters_data:
        processed.append({
            "name": c.get("name"),
            "gender": c.get("gender"),
            "birth_year": c.get("birth_year"),
        })
    store_objects(db, Character, processed, "name")

# -------------------- Films --------------------
def fetch_films():
    """
    Fetch films from SWAPI.

    Returns:
        list: List of film dicts
    """
    return fetch_from_swapi("films")

def store_films(db: Session, films_data):
    """
    Store films into the database.

    Args:
        db (Session): Database session
        films_data (list): List of film dicts

    Returns:
        None
    """
    processed = []
    for f in films_data:
        processed.append({
            "title": f.get("title"),
            "director": f.get("director"),
            "release_date": f.get("release_date"),
        })
    store_objects(db, Film, processed, "title")

# -------------------- Starships --------------------
def fetch_starships():
    """
    Fetch starships from SWAPI.

    Returns:
        list: List of starship dicts
    """
    return fetch_from_swapi("starships")

def store_starships(db: Session, starships_data):
    """
    Store starships into the database.

    Args:
        db (Session): Database session
        starships_data (list): List of starship dicts

    Returns:
        None
    """
    processed = []
    for s in starships_data:
        processed.append({
            "name": s.get("name"),
            "model": s.get("model"),
            "manufacturer": s.get("manufacturer"),
        })
    store_objects(db, Starship, processed, "name")

# -------------------- Relationship Filler --------------------
def fill_relationships(db: Session):
    """
    Fill many-to-many relationships between characters, films, and starships.

    Args:
        db (Session): Database session

    Returns:
        None
    """
    try:
        characters = db.query(Character).all()
        films = db.query(Film).all()
        starships = db.query(Starship).all()

        for c in characters:
            for f in films:
                if f not in c.films:
                    c.films.append(f)
            for s in starships:
                if s not in c.starships:
                    c.starships.append(s)
        for f in films:
            for s in starships:
                if s not in f.starships:
                    f.starships.append(s)
        db.commit()
        logging.info("Relationships filled successfully.")
    except Exception as e:
        db.rollback()
        handle_db_exception(e, context="filling relationships")
        raise
