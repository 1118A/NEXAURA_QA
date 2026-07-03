import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask

from app.config import LOGS_DIR, check_config, CONFIG_ERRORS

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    
    # 1. Setup Logging
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "app.log"
    
    log_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s"
    )
    
    # File handler (rotate logs at 5MB, keep 3 backup files)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logging.info("Logging initialized.")

    # 2. Check Configuration (Log error and warning flags, but don't prevent startup)
    if CONFIG_ERRORS:
        logging.warning(
            "Application started with configuration warnings: " + ", ".join(CONFIG_ERRORS)
        )
    else:
        logging.info("Environment configuration checked and validated successfully.")

    # 3. Register Blueprint/Routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    logging.info("Flask application created and configured.")
    return app
