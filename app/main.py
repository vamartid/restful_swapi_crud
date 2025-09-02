import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from app.database import init_db
from app.routes import swapi_routes
from app.logging_config import setup_logging, logging
from scripts.load_utils import load_config_ini
from app.db_exceptions import handle_db_exception


# -------------------- Configuration Loader --------------------
def load_configuration() -> dict:
    """Load DB configuration from .ini file or environment variables."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ini_path = os.path.join(project_root, ".ini")
    logging.info(f"Looking for config.ini at: {ini_path}")

    cfg = load_config_ini(ini_path)
    if cfg:
        logging.info(f"Using database configuration from {ini_path}")
        config = {
            "DB_USER": cfg.get("db_user"),
            "DB_PASSWORD": cfg.get("db_password"),
            "DB_HOST": cfg.get("host", "localhost"),
            "DB_NAME": cfg.get("db_name"),
            "DB_PORT": int(cfg.get("port", 3306)),
        }
    else:
        logging.info("No .ini found, falling back to environment variables")
        config = {
            "DB_USER": os.getenv("DB_USER"),
            "DB_PASSWORD": os.getenv("DB_PASSWORD"),
            "DB_HOST": os.getenv("DB_HOST", "localhost"),
            "DB_NAME": os.getenv("DB_NAME"),
            "DB_PORT": int(os.getenv("DB_PORT", 3306)),
        }

    # Validate required variables
    if not all([config["DB_USER"], config["DB_PASSWORD"], config["DB_NAME"]]):
        raise RuntimeError("Missing required database configuration (user/password/db_name)")

    return config


# -------------------- Database Initializer --------------------
def initialize_database(config: dict):
    """Initialize the database connection."""
    try:
        init_db(
            config["DB_USER"],
            config["DB_PASSWORD"],
            config["DB_HOST"],
            config["DB_NAME"],
            config["DB_PORT"],
        )
        logging.info("Database connection initialized successfully")
    except Exception as e:
        handle_db_exception(e, context="initializing database", exit_on_error=False)


# -------------------- FastAPI App Factory --------------------
def create_app(config: dict = None) -> FastAPI:
    """Factory to create FastAPI app with exception handlers and routes."""
    # Setup logging
    setup_logging(log_to_terminal=True, log_to_file=True)

    app = FastAPI(title="SWAPI CRUD API")
    app.include_router(swapi_routes.router)

    # Exception handlers
    @app.exception_handler(SQLAlchemyError)
    async def db_exception_handler(request: Request, exc: SQLAlchemyError):
        logging.error(f"Database error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Database error occurred. Please check logs."},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logging.warning(f"HTTP Exception: {exc.detail}")
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logging.error(f"Unhandled error: {exc}")
        return JSONResponse(status_code=500, content={"detail": "Internal server error. Check logs."})

    # Optionally initialize DB (only if config provided)
    if config:
        initialize_database(config)

    return app


# -------------------- App instance --------------------
config = load_configuration()
app = create_app(config)
