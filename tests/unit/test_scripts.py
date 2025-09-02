# tests/test_db_scripts.py

import pytest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os

from scripts.args_utils import parse_db_arguments
from scripts.create_db import create_database
from scripts.create_tables import create_tables
from scripts.delete_db import drop_database
from scripts.load_db_config import get_db_config
from scripts.load_utils import load_config_ini


# ---------------------- create_database / drop_database ----------------------
@patch("scripts.create_db.pymysql.connect")
@patch("scripts.create_db.logging.info")
def test_create_database_success(mock_log, mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    create_database(
        host="localhost",
        port=3306,
        root_user="root",
        root_password="rootpass",
        db_name="test_db",
        db_user="test_user",
        db_password="pass123"
    )
    mock_connect.assert_called_once_with(host="localhost", user="root", password="rootpass", port=3306)
    assert mock_log.called

@patch("scripts.delete_db.pymysql.connect")
@patch("scripts.delete_db.logging.info")
def test_drop_database_success(mock_log, mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    drop_database(
        host="localhost",
        port=3306,
        root_user="root",
        root_password="rootpass",
        db_name="test_db"
    )
    mock_connect.assert_called_once()
    assert mock_log.called


# ---------------------- main (create_tables) ----------------------
# ---------------------- main (create_tables) ----------------------
@patch("app.database.Base")              # patch Base from app.database
@patch("app.database.init_db")           # patch init_db where it's actually defined
@patch("scripts.create_tables.logging.info")  # patch logging in the script module
def test_main_creates_tables(mock_log, mock_init_db, mock_base):
    # Mock engine returned by init_db
    mock_engine = MagicMock()
    mock_init_db.return_value = mock_engine

    # Call the function
    create_tables(
        db_user="test_user",
        db_password="pass123",
        db_host="localhost",
        db_name="test_db",
        db_port=3306
    )

    # Assertions
    mock_init_db.assert_called_once_with("test_user", "pass123", "localhost", "test_db", 3306)
    assert mock_base.metadata.create_all.called
    assert mock_base.metadata.create_all.call_args[1]["bind"] == mock_engine
    assert mock_log.called
	
# ---------------------- parse_db_arguments ----------------------

def test_parse_db_arguments_defaults(monkeypatch):
    monkeypatch.setattr(
        sys, "argv",
        [
            "prog",
            "--db_host", "localhost",
            "--db_port", "3306",
            "--db_name", "swapi_db",
            "--db_user", "swapi_user",
            "--db_password", "1234"  # required
        ]
    )
    args = parse_db_arguments()
    assert args.db_host == "localhost"
    assert args.db_name == "swapi_db"
    assert args.db_user == "swapi_user"
    assert args.db_password == "1234"
	
def test_parse_db_arguments_require_root(monkeypatch):
    monkeypatch.setattr(
        sys, "argv",
        [
            "prog",
            "--db_host", "localhost",
            "--db_port", "3306",
            "--db_name", "swapi_db",
            "--db_user", "swapi_user",
            "--db_password", "1234",      # <-- comma added here
            "--root_user", "root",
            "--root_password", "rootpass"
        ]
    )
    args = parse_db_arguments(require_root=True)
    assert args.db_host == "localhost"
    assert args.db_name == "swapi_db"
    assert args.db_user == "swapi_user"
    assert args.db_password == "1234"
    assert args.root_user == "root"
    assert args.root_password == "rootpass"


# ---------------------- load_config_ini ----------------------

@patch("os.path.exists", return_value=True)  # ensure the file is "found"
@patch("builtins.open", new_callable=mock_open, read_data="[database]\nDB_HOST=127.0.0.1\nDB_PORT=3306\nDB_NAME=test_db\nDB_USER=test_user\nDB_PASSWORD=pass\nROOT_USER=root\nROOT_PASSWORD=rootpass")
def test_load_config_ini(mock_file, mock_exists):
    path = "fake_path.ini"
    cfg = load_config_ini(path)
    assert cfg["host"] == "127.0.0.1"
    assert cfg["port"] == 3306
    assert cfg["db_name"] == "test_db"
    assert cfg["db_user"] == "test_user"
    assert cfg["db_password"] == "pass"

@patch("os.path.exists", return_value=False)
def test_load_config_ini_missing(mock_exists):
    cfg = load_config_ini("nonexistent.ini")
    assert cfg is None


# ---------------------- get_db_config ----------------------
import pytest
from unittest.mock import patch, MagicMock
from scripts.load_db_config import get_db_config

# ---------------------- Use .ini ----------------------
# Patch load_config_ini where it is used (inside load_db_config)
@patch("scripts.load_utils.load_config_ini")
def test_get_db_config_uses_ini(mock_load_ini):
    mock_load_ini.return_value = {
        "db_user": "u",
        "db_password": "p",
        "host": "localhost",
        "db_name": "db",
        "port": 3306,
    }

    cfg = get_db_config()
    assert cfg["host"] == "localhost"
    mock_load_ini.assert_called_once()
	
@patch("scripts.args_utils.parse_db_arguments")
@patch("scripts.load_utils.load_config_ini", return_value=None)
def test_get_db_config_uses_args(mock_load_ini, mock_parse_args):
    # Simulate parsed args
    mock_parse_args.return_value = MagicMock(
        db_host="localhost",
        db_port=3306,
        db_user="u",
        db_password="p",
        db_name="db"
    )

    cfg = get_db_config()

    assert cfg["db_host"] == "localhost"
    assert cfg["db_user"] == "u"
    assert cfg["db_password"] == "p"
    assert cfg["db_name"] == "db"

    mock_load_ini.assert_called_once()
    mock_parse_args.assert_called_once()