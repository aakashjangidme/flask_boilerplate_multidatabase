import logging
import os
from typing import Optional
from flask import Flask, g


from app.utils.logger_ext.logger import setup_logger_ext
from app.config import config
from .middleware import (
    register_middlewares,
)


logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)
    env = os.getenv("FLASK_ENV", "development")
    app.config.from_object(config[env])

    # Setup logging
    setup_logger_ext()

    logger.info(f"Starting Flask app in {env} environment")

    # Register middleware
    register_middlewares(app)

    # Register routes
    from .routes import api

    app.register_blueprint(api)

    return app
