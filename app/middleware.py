import time
from typing import Optional
from uuid import uuid4
from flask import Flask, g, request, Response
import logging

from app.database import DatabaseManager


logger = logging.getLogger()


def log_request_start() -> None:
    g.start_time = time.perf_counter()


def add_request_id() -> None:
    g.request_id = request.headers.get("X-Request-ID", str(uuid4()))


def log_request_end(response: Response) -> Response:
    """
    Logs the request duration and closes the database connections.

    :param response: The response object from the request.
    :return: The same response object.
    """
    duration = (time.perf_counter() - g.pop("start_time", 0)) * 1000

    logger.info(
        f"{duration:.2f}ms {request.method} {request.path} {response.status} {dict(request.args)}",
        extra={"skip_module_func": True},
    )

    response.headers["X-Request-ID"] = g.request_id
    return response


def teardown_db(exception: Optional[Exception]) -> None:
    """
    Closes all database connections at the end of the request context.

    :param exception: Any exception raised during the request.
    """
    db_manager = g.pop("db_manager", None)
    if db_manager:
        db_manager.close_connections()


def register_middlewares(app: Flask) -> None:
    app.before_request(log_request_start)
    app.before_request(add_request_id)
    app.after_request(log_request_end)

    @app.before_request
    def load_database() -> None:
        """
        Ensure DatabaseManager is initialized.
        """
        if "db_manager" not in g:
            g.db_manager = DatabaseManager(app.config)

    app.teardown_appcontext(teardown_db)
