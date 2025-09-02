def get_db_config(require_root=False, expected_keys=None):
    """
    Returns a dict of database config parameters.

    - require_root: whether root credentials are required (for create/drop)
    - expected_keys: optional list of keys to pass to target function
    """
    from scripts.args_utils import parse_db_arguments
    from scripts.load_utils import load_config_ini
    import os
    import logging
    
    ini_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".ini")
    logging.info(f"Looking for config.ini at: {ini_path}")
    
    cfg = load_config_ini(ini_path)
    if cfg:
        logging.info(f"Using database configuration from {ini_path}")
    else:
        logging.info("No .ini found, using command-line arguments")
        args = parse_db_arguments(require_root=require_root)
        cfg = vars(args)  # convert Namespace -> dict

    # Filter keys if expected_keys is provided
    if expected_keys:
        cfg = {k: cfg[k] for k in expected_keys if k in cfg}
    
    return cfg
