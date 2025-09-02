# SWAPI CRUD API
## Overview
`SWAPI CRUD API` is a FastAPI application providing CRUD operations and integration with the **Star Wars API (SWAPI)**.
It supports database persistence, centralized logging, and modular design.
## Features
- Fetch, read, and manipulate SWAPI data.
- Database CRUD operations using MySQL.
- Synchronize all SWAPI data via `swapi_sync.sync_all`.
- Centralized logging to **terminal** and **log file**.
- FastAPI exception handling for:
  - SQLAlchemy database errors
  - HTTP errors
  - General unhandled exceptions
- Configuration management** via `.ini` file or environment variables.
- Modular structure: separate **routes**, **services**, **database**, and **utilities**.
- Unit tests with >90% coverage.

## Project Structure
```text
app/
├─ main.py               # FastAPI entrypoint, exception handlers, DB init
├─ database.py           # Database initialization utilities
├─ db_exceptions.py      # Custom exception handling for DB-related errors
├─ logging_config.py     # Logging setup (console + file)
├─ models.py             # SQLAlchemy models
├─ routes/
│  └─ swapi_routes.py    # API routes (CRUD endpoints)
├─ services/
│  ├─ swapi_service.py   # Service layer with DB operations
│  └─ swapi_sync.py      # Contains sync_all function for syncing SWAPI data
scripts/
├─ create_db.py          # Script to create database
├─ create_tables.py      # Script to create tables
├─ delete_db.py          # Script to delete database
├─ args_utils.py         # Utilities for parsing CLI args
├─ load_db_config.py     # Load DB config from ini/env
├─ load_utils.py         # Config loading helpers
tests/
├─ unit/                 
│  ├─ test_database.py        # Unit tests for database.py
│  ├─ test_db_exceptions.py   # Unit tests for db_exceptions.py
│  ├─ test_logging_config.py  # Unit tests for logging setup
│  ├─ test_models.py          # Unit tests for SQLAlchemy models
│  ├─ test_scripts.py         # Unit tests for CLI scripts
│  ├─ test_swapi_main.py      # Unit tests for FastAPI main app
│  ├─ test_swapi_routes.py    # Unit tests for API routes
│  └─ test_swapi_service.py   # Unit tests for service layer
logs/
├─ app.log (will be created)   # Application logs
├─ uvicorn.log (will be created) # Uvicorn server logs
requirements.txt               # Main dependencies
```
## Configuration
You can use a `.ini` file to configure DB credentials:

**`config.ini` example:**

```ini
[database]
DB_USER = swapi_user
DB_PASSWORD = 1234
DB_HOST = localhost
DB_NAME = swapi_db
DB_PORT = 3306
ROOT_USER = root
ROOT_PASSWORD = 1234
```

If no `.ini` is provided, environment variables will be used:

```bash
export DB_USER=swapi_user
export DB_PASSWORD=1234
export DB_HOST=localhost
export DB_NAME=swapi_db
export DB_PORT=3306
export ROOT_USER=root
export ROOT_PASSWORD=1234
```

---

## Logging
- Logs are written to both **terminal** and **log file**.
- Levels:
  - **INFO**: DB and table operations
  - **WARNING**: recoverable errors
  - **ERROR**: unhandled exceptions or DB failures

---

## Scripts

### Run scripts with arguments
```bash
python -m scripts.create_db --db_host localhost --db_port 3306 --db_name dummy_db --db_user dummy_user --db_password dummy_pass --root_user root --root_password root_pass

python -m scripts.create_tables --db_host localhost --db_port 3306 --db_name dummy_db --db_user dummy_user --db_password dummy_pass

python -m scripts.delete_db --db_host localhost --db_port 3306 --db_name dummy_db --db_user dummy_user --db_password dummy_pass --root_password root_pass
```

### Run scripts using `.ini`
```bash
python -m scripts.create_db
python -m scripts.create_tables
python -m scripts.delete_db
```

---

## Usage

### Start FastAPI app
- Without `.ini`:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- With `.ini`:
```bash
uvicorn app.main:app --reload
```

### Access API docs
```
http://127.0.0.1:8000/docs
```

---

## Testing

### Unit tests
- Set `PYTHONPATH` if needed:
```powershell
$env:PYTHONPATH = (Get-Location)   # PowerShell
```
```cmd
set PYTHONPATH=%cd%                # CMD
```
- Run tests:
```bash
pytest -q --show-capture=no --disable-warnings .\tests\unit\
...................................................................
[100%] 67 passed in 1.39s    

```

### Coverage
- Run coverage
```bash
coverage run --source=.\app\ -m pytest -v .\tests\unit\
```
- Print coverage
```bash
coverage report -m
```
```
Example coverage report (we are over 80%):
Name                            Stmts   Miss  Cover   Missing
-------------------------------------------------------------
app\__init__.py                     0      0   100%
app\database.py                    21      4    81%   31-35
app\db_exceptions.py               26      2    92%   51, 64
app\logging_config.py              33      0   100%
app\main.py                        49      0   100%
app\models.py                      30      0   100%
app\routes\__init__.py              0      0   100%
app\routes\swapi_routes.py        104      5    95%   23, 28, 60, 92, 124
app\services\__init__.py            0      0   100%
app\services\swapi_service.py      85     13    85%   43, 51, 65-68, 73, 88, 103, 136-139
app\services\swapi_sync.py          9      0   100%
-------------------------------------------------------------
TOTAL                             357     24    93%
```

Unit tests cover services, main app initialization, scripts, and DB-related functionality. Integration tests are not included in coverage.