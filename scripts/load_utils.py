def load_config_ini(path):
    import configparser, os
    if not os.path.exists(path):
        return None
    config = configparser.ConfigParser()
    config.read(path)
    if "database" not in config:
        return None
    db_cfg = config["database"]
    return {
        "host": db_cfg.get("DB_HOST", "localhost"),
        "port": int(db_cfg.get("DB_PORT", 3306)),
        "root_user": db_cfg.get("ROOT_USER", "root"),
        "root_password": db_cfg.get("ROOT_PASSWORD", ""),
        "db_name": db_cfg.get("DB_NAME", "swapi_db"),
        "db_user": db_cfg.get("DB_USER", "swapi_user"),
        "db_password": db_cfg.get("DB_PASSWORD", ""),
    }
