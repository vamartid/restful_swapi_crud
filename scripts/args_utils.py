def parse_db_arguments(require_root=False):
    """
    Returns parsed database arguments.
    If require_root is True, root_user and root_password are required (for create_db).
    """
    import argparse
    parser = argparse.ArgumentParser(description="Database arguments for SWAPI project")
    
    args_map = {
        "db_host": ("localhost", "Database host", False),
        "db_port": (3306, "Database port", False),
        "db_name": ("swapi_db", "Database name", False),
        "db_user": ("swapi_user", "Database username", False),
        "db_password": (None, "Database user password", True),
    }
    
    if require_root:
        args_map.update({
            "root_user": ("root", "Root username", False),
            "root_password": (None, "Root password", True),
        })
    
    for arg, (default, help_text, required) in args_map.items():
        parser.add_argument(
            f"--{arg}",
            default=default,
            help=help_text,
            required=required,
            type=type(default) if default is not None else str,
        )
    
    return parser.parse_args()
