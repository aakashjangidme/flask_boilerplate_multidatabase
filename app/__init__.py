import logging
import os

from flask import Flask


from app.database.db_manager import DatabaseManager
from app.utils.logger_ext.logger import setup_logger_ext
from app.config import config
from .middleware import (
    register_middlewares,
)


logger = logging.getLogger(__name__)

db = DatabaseManager()


def create_app() -> Flask:
    app = Flask(__name__)
    env = os.getenv("FLASK_ENV", "development")
    app.config.from_object(config[env])

    # Setup logging
    setup_logger_ext()

    logger.info(f"Starting Flask app in {env} environment")

    # Register middleware
    register_middlewares(app)

    db.init_app(app)

    # health_check()

    # Register routes
    from .routes import api

    app.register_blueprint(api)

    return app


def health_check():
    if db.postgres:
        postgres_healthy = db.postgres.fetch_one("select 1 as _health")
        db.close_connections()

    if not postgres_healthy:
        logger.error("PostgreSQL connection is not healthy.")
        exit(1)
