import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import create_app, load_configuration, initialize_database


# -------------------- Fixture for app --------------------
@pytest.fixture
def app():
    return create_app(config=None)

@pytest.fixture
def client(app):
    # Disable exception propagation to test handlers
    return TestClient(app, raise_server_exceptions=False)


# -------------------- Test configuration loader --------------------
def test_load_configuration_ini(monkeypatch):
    # Mock load_config_ini to return a fake config
    fake_config = {
        "db_user": "user",
        "db_password": "pass",
        "db_name": "dbname",
        "host": "localhost",
        "port": "3306",
    }

    with patch("app.main.load_config_ini", return_value=fake_config):
        config = load_configuration()
        assert config["DB_USER"] == "user"
        assert config["DB_PASSWORD"] == "pass"
        assert config["DB_NAME"] == "dbname"
        assert config["DB_HOST"] == "localhost"
        assert config["DB_PORT"] == 3306


def test_load_configuration_env(monkeypatch):
    # Remove any .ini config by patching load_config_ini
    with patch("app.main.load_config_ini", return_value=None):
        # Set environment variables
        monkeypatch.setenv("DB_USER", "env_user")
        monkeypatch.setenv("DB_PASSWORD", "env_pass")
        monkeypatch.setenv("DB_NAME", "env_db")

        config = load_configuration()
        assert config["DB_USER"] == "env_user"
        assert config["DB_PASSWORD"] == "env_pass"
        assert config["DB_NAME"] == "env_db"

def test_load_configuration_missing_required(monkeypatch):
    from app.main import load_configuration
    # Patch load_config_ini to return None
    with patch("app.main.load_config_ini", return_value=None):
        # Remove environment variables individually
        monkeypatch.delenv("DB_USER", raising=False)
        monkeypatch.delenv("DB_PASSWORD", raising=False)
        monkeypatch.delenv("DB_NAME", raising=False)

        import pytest
        with pytest.raises(RuntimeError, match="Missing required database configuration"):
            load_configuration()


# -------------------- Test database initializer --------------------
def test_initialize_database_calls_init_db(monkeypatch):
    fake_config = {
        "DB_USER": "user",
        "DB_PASSWORD": "pass",
        "DB_HOST": "localhost",
        "DB_NAME": "dbname",
        "DB_PORT": 3306,
    }

    mock_init_db = MagicMock()
    with patch("app.main.init_db", mock_init_db):
        initialize_database(fake_config)
        mock_init_db.assert_called_once_with(
            "user", "pass", "localhost", "dbname", 3306
        )

def test_initialize_database_handles_exception():
    from app.main import initialize_database
    from unittest.mock import patch

    fake_config = {
        "DB_USER": "user",
        "DB_PASSWORD": "pass",
        "DB_HOST": "localhost",
        "DB_NAME": "dbname",
        "DB_PORT": 3306,
    }

    def raise_error(*args, **kwargs):
        raise RuntimeError("DB fail")

    with patch("app.main.init_db", raise_error), \
         patch("app.main.handle_db_exception") as mock_handle:
        initialize_database(fake_config)

        mock_handle.assert_called_once()
        pos_args, kw_args = mock_handle.call_args
        assert isinstance(pos_args[0], RuntimeError)
        assert kw_args["context"] == "initializing database"
        assert kw_args["exit_on_error"] is False

# -------------------- Test app with database initializer --------------------
def test_create_app_with_db_initialization():
    fake_config = {
        "DB_USER": "user",
        "DB_PASSWORD": "pass",
        "DB_HOST": "localhost",
        "DB_NAME": "dbname",
        "DB_PORT": 3306,
    }

    mock_init_db = MagicMock()
    with patch("app.main.init_db", mock_init_db):
        app = create_app(config=fake_config)
        mock_init_db.assert_called_once_with(
            "user", "pass", "localhost", "dbname", 3306
        )


# -------------------- Test exception handlers --------------------
def test_exception_handlers_registered(client):
    app = client.app
    handlers = getattr(app, "exception_handlers", {})
    handler_classes = list(handlers.keys())

    # Check that the handlers are registered
    assert any(issubclass(cls, SQLAlchemyError) for cls in handler_classes)
    assert any(issubclass(cls, HTTPException) for cls in handler_classes)
    assert any(cls is Exception for cls in handler_classes)


def test_db_exception_handler(client):
    @client.app.get("/raise-db-error")
    async def raise_db_error():
        raise SQLAlchemyError("DB fail")

    response = client.get("/raise-db-error")
    assert response.status_code == 500
    assert response.json()["detail"] == "Database error occurred. Please check logs."


def test_http_exception_handler(client):
    @client.app.get("/raise-http-error")
    async def raise_http_error():
        raise HTTPException(status_code=404, detail="Not found")

    response = client.get("/raise-http-error")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not found"
	
def test_general_exception_handler(client):
	@client.app.get("/raise-general-error")
	async def raise_general_error():
		raise ValueError("Oops")

	response = client.get("/raise-general-error")
	assert response.status_code == 500
	assert response.json()["detail"] == "Internal server error. Check logs."
