import logging
import os
import time
from uuid import uuid4
from flask import Flask, g, jsonify, request, Response
from typing import Optional

from app.database import DatabaseManager
from app.config import config
from app.utils.logger_ext.logger import setup_logger_ext

# Initialize logger
logger = logging.getLogger()

# Initialize Flask app
app = Flask(__name__)
env = os.getenv("FLASK_ENV", "development")
app.config.from_object(config[env])

# Setup logging
setup_logger_ext()


def get_db() -> DatabaseManager:
    """
    Retrieves the DatabaseManager instance for the current application context.

    :return: An instance of DatabaseManager.
    """
    if "db_manager" not in g:
        g.db_manager = DatabaseManager(config=app.config)
    return g.db_manager


@app.teardown_appcontext
def teardown_db(exception: Optional[BaseException]) -> None:
    """
    Closes all database connections at the end of the request context.

    :param exception: Any exception raised during the request.
    """
    db_manager = g.pop("db_manager", None)
    if db_manager:
        db_manager.close_connections()


@app.before_request
def log_route_start() -> None:
    """
    Records the start time of the request for logging purposes.
    """
    g.start_time = time.perf_counter()


@app.before_request
def before_load_request() -> None:
    """
    Sets a unique request ID for the request.
    """
    g.request_id = request.headers.get("X-Request-ID", str(uuid4()))


@app.after_request
def after_load_request(response: Response) -> Response:
    """
    Adds the request ID to the response headers.

    :param response: The response object to return.
    :return: The response object.
    """
    response.headers["X-Request-ID"] = g.request_id
    return response


@app.after_request
def log_route_end(response: Response) -> Response:
    """
    Logs the duration of the request processing.

    :param response: The response object to return.
    :return: The response object.
    """
    duration: float = (time.perf_counter() - g.pop("start_time", 0)) * 1000
    logger.info(
        f"{duration:.2f}ms {request.method} {request.path} {dict(request.args)}"
    )
    return response


@app.route("/")
def index():
    """
    Index route that returns database session information.

    :return: A dictionary containing the session user and database name.
    """
    db = get_db()
    response = None
    if db.postgres:
        response = db.postgres.fetch_one("SELECT session_user, current_database()")

    return jsonify(data=response), 200


if __name__ == "__main__":
    app.run()
