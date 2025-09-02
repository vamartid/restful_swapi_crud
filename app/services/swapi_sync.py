def sync_all(db):
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
