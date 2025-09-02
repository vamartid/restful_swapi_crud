"""
SWAPI synchronization orchestrator.

Provides functions to fetch and store SWAPI entities (characters, films, starships)
and populate the many-to-many relationships in the database.
"""

def sync_all(db):
    """
    Fetch all SWAPI entities and store them in the database, including
    filling many-to-many relationships between characters, films, and starships.

    Args:
        db (Session): SQLAlchemy database session

    Returns:
        None

    Raises:
        Exception: If any fetch/store operation or relationship filling fails
    """
    from app.services.swapi_service import (
        fetch_characters, store_characters,
        fetch_films, store_films,
        fetch_starships, store_starships,
        fill_relationships
    )

    # Fetch and store base entities
    chars = fetch_characters()
    store_characters(db, chars)

    films = fetch_films()
    store_films(db, films)

    ships = fetch_starships()
    store_starships(db, ships)

    # Populate association tables
    fill_relationships(db)
