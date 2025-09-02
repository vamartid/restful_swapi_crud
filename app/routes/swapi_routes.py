from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from functools import wraps
from app.database import get_db
from app.models import Character, Film, Starship
import app.services.swapi_service as swapi
from app.services.swapi_sync import sync_all
import logging
from app.db_exceptions import handle_db_exception

LOG_FETCHED_OBJECTS = True  # Set to False to disable logging

# -------------------- Decorator --------------------
def safe_route(func):
    """
    Decorator for route functions to add:
    - try/except error handling
    - logging for errors and empty results
    - input validation for skip/limit parameters
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Validate skip/limit if present
            if "skip" in kwargs and kwargs["skip"] > 10000:
                raise HTTPException(status_code=400, detail="Skip value too large")
            if "limit" in kwargs and ("limit" in kwargs) and (kwargs["limit"] < 1 or kwargs["limit"] > 100):
                raise HTTPException(status_code=400, detail="Limit must be 1–100")

            result = func(*args, **kwargs)

            if isinstance(result, list) and not result:
                logging.info(f"{func.__name__}: no data found")

            return result

        except HTTPException:
            raise  # propagate proper FastAPI exceptions
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {e}")
            try:
                handle_db_exception(e, exit_on_error=False)
            except Exception:
                pass
            raise HTTPException(status_code=500, detail=f"Internal error in {func.__name__}")

    return wrapper

# -------------------- Router --------------------
router = APIRouter(prefix="/swapi", tags=["SWAPI"])

# -------------------- Orchestrator --------------------
@router.post("/sync/all")
@safe_route
def sync_all_endpoint(db: Session = Depends(get_db)):
    """
    Sync all SWAPI resources into the database.

    - **db**: Database session (Dependency Injection)
    - **Returns**: Message indicating successful sync
    """
    sync_all(db)
    return {"message": "All SWAPI data synced successfully"}

# -------------------- Characters --------------------
@router.post("/sync/characters")
@safe_route
def sync_characters(db: Session = Depends(get_db)):
    """
    Fetch characters from SWAPI and store them in the database.

    - **db**: Database session
    - **Returns**: Message with number of characters synced or info if none found
    """
    characters = swapi.fetch_characters()
    if not characters:
        return {"message": "No characters found to sync"}
    swapi.store_characters(db, characters)
    return {"message": f"{len(characters)} characters synced successfully"}

@router.get("/characters")
@safe_route
def get_characters(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, gt=0, le=100, description="Number of records to return")
):
    """
    Retrieve characters from the database.

    - **skip**: Number of records to skip
    - **limit**: Number of records to return (1–100)
    - **Returns**: List of characters with related films and starships
    """
    chars = db.query(Character).offset(skip).limit(limit).all()
    if LOG_FETCHED_OBJECTS and chars:
        logging.info("Fetched: " + " | ".join(c.name for c in chars))
    return [
        {
            "id": c.id,
            "name": c.name,
            "gender": c.gender,
            "birth_year": c.birth_year,
            "films": [{"id": f.id, "title": f.title} for f in c.films],
            "starships": [{"id": s.id, "name": s.name} for s in c.starships],
        }
        for c in chars
    ]

# -------------------- Films --------------------
@router.post("/sync/films")
@safe_route
def sync_films(db: Session = Depends(get_db)):
    """
    Fetch films from SWAPI and store them in the database.

    - **db**: Database session
    - **Returns**: Message with number of films synced or info if none found
    """
    films = swapi.fetch_films()
    if not films:
        return {"message": "No films found to sync"}
    swapi.store_films(db, films)
    return {"message": f"{len(films)} films synced successfully"}

@router.get("/films")
@safe_route
def get_films(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, gt=0, le=100, description="Number of records to return")
):
    """
    Retrieve films from the database.

    - **skip**: Number of records to skip
    - **limit**: Number of records to return (1–100)
    - **Returns**: List of films with related characters and starships
    """
    films = db.query(Film).offset(skip).limit(limit).all()
    if LOG_FETCHED_OBJECTS and films:
        logging.info("Fetched: " + " | ".join(f.title for f in films))
    return [
        {
            "id": f.id,
            "title": f.title,
            "director": f.director,
            "release_date": f.release_date,
            "characters": [{"id": c.id, "name": c.name} for c in f.characters],
            "starships": [{"id": s.id, "name": s.name} for s in f.starships],
        }
        for f in films
    ]

# -------------------- Starships --------------------
@router.post("/sync/starships")
@safe_route
def sync_starships(db: Session = Depends(get_db)):
    """
    Fetch starships from SWAPI and store them in the database.

    - **db**: Database session
    - **Returns**: Message with number of starships synced or info if none found
    """
    starships = swapi.fetch_starships()
    if not starships:
        return {"message": "No starships found to sync"}
    swapi.store_starships(db, starships)
    return {"message": f"{len(starships)} starships synced successfully"}

@router.get("/starships")
@safe_route
def get_starships(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, gt=0, le=100, description="Number of records to return")
):
    """
    Retrieve starships from the database.

    - **skip**: Number of records to skip
    - **limit**: Number of records to return (1–100)
    - **Returns**: List of starships with related characters and films
    """
    starships = db.query(Starship).offset(skip).limit(limit).all()
    if LOG_FETCHED_OBJECTS and starships:
        logging.info("Fetched: " + " | ".join(s.name for s in starships))
    return [
        {
            "id": s.id,
            "name": s.name,
            "model": s.model,
            "manufacturer": s.manufacturer,
            "characters": [{"id": c.id, "name": c.name} for c in s.characters],
            "films": [{"id": f.id, "title": f.title} for f in s.films],
        }
        for s in starships
    ]

# -------------------- Search --------------------
@router.get("/characters/search")
@safe_route
def search_characters(
    name: str = Query(..., min_length=1, description="Name or partial name to search for"),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, gt=0, le=100, description="Number of records to return")
):
    """
    Search characters by name (partial or full).

    - **name**: Name or partial name to search for
    - **skip**: Number of records to skip
    - **limit**: Number of records to return
    - **Returns**: List of matching characters with related films and starships
    """
    chars = db.query(Character).filter(Character.name.ilike(f"%{name}%")).offset(skip).limit(limit).all()
    if LOG_FETCHED_OBJECTS and chars:
        logging.info("Fetched: " + " | ".join(c.name for c in chars))
    return [
        {
            "id": c.id,
            "name": c.name,
            "gender": c.gender,
            "birth_year": c.birth_year,
            "films": [{"id": f.id, "title": f.title} for f in c.films],
            "starships": [{"id": s.id, "name": s.name} for s in c.starships],
        }
        for c in chars
    ]

@router.get("/films/search")
@safe_route
def search_films(
    title: str = Query(..., min_length=1, description="Title or partial title to search for"),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, gt=0, le=100, description="Number of records to return")
):
    """
    Search films by title (partial or full).

    - **title**: Title or partial title to search for
    - **skip**: Number of records to skip
    - **limit**: Number of records to return
    - **Returns**: List of matching films with related characters and starships
    """
    films = db.query(Film).filter(Film.title.ilike(f"%{title}%")).offset(skip).limit(limit).all()
    if LOG_FETCHED_OBJECTS and films:
        logging.info("Fetched: " + " | ".join(f.title for f in films))
    return [
        {
            "id": f.id,
            "title": f.title,
            "director": f.director,
            "release_date": f.release_date,
            "characters": [{"id": c.id, "name": c.name} for c in f.characters],
            "starships": [{"id": s.id, "name": s.name} for s in f.starships],
        }
        for f in films
    ]

@router.get("/starships/search")
@safe_route
def search_starships(
    name: str = Query(..., min_length=1, description="Name or partial name to search for"),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, gt=0, le=100, description="Number of records to return")
):
    """
    Search starships by name (partial or full).

    - **name**: Name or partial name to search for
    - **skip**: Number of records to skip
    - **limit**: Number of records to return
    - **Returns**: List of matching starships with related characters and films
    """
    starships = db.query(Starship).filter(Starship.name.ilike(f"%{name}%")).offset(skip).limit(limit).all()
    if LOG_FETCHED_OBJECTS and starships:
        logging.info("Fetched: " + " | ".join(s.name for s in starships))
    return [
        {
            "id": s.id,
            "name": s.name,
            "model": s.model,
            "manufacturer": s.manufacturer,
            "characters": [{"id": c.id, "name": c.name} for c in s.characters],
            "films": [{"id": f.id, "title": f.title} for f in s.films],
        }
        for s in starships
    ]
