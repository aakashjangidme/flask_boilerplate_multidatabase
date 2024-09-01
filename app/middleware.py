
import time
from uuid import uuid4
from flask import Flask, g, jsonify, request, Response
import logging
from werkzeug.exceptions import HTTPException

from app.exceptions import APIException

# Configure logging
logger = logging.getLogger(__name__)


def log_request_start() -> None:
    """Log the start time of the request."""
    g.start_time = time.perf_counter()


def add_request_id() -> None:
    """Add a unique request ID to the request context and log the start of the request."""
    g.request_id = request.headers.get("X-Request-ID", str(uuid4()))

    logger.info(
        f"<--BEGIN: {request.method} {request.path} {dict(request.args)}",
        extra={"skip_module_func": True, "request_id": g.request_id},
    )


def log_request_end(response: Response) -> Response:
    """
    Logs the request duration and attaches the request ID to the response.

    :param response: The response object from the request.
    :return: The same response object with additional headers.
    """
    duration = (time.perf_counter() - g.pop("start_time", 0)) * 1000

    logger.info(
        f"{duration:.2f} ms {request.method} {request.path} {response.status} {dict(request.args)} :END-->",
        extra={"skip_module_func": True, "request_id": g.get("request_id", "-")},
    )

    response.headers["X-Request-ID"] = g.request_id
    return response


def create_error_response(error_message: str, status_code: int) -> Response:
    """Utility function to create a JSON response for errors."""
    response = jsonify({"error": error_message, "status_code": status_code})
    response.status_code = status_code
    return response


def handle_api_exception(error: APIException) -> Response:
    """Handle API exceptions."""
    return create_error_response(error.message, error.status_code)


def handle_http_exception(error: HTTPException) -> Response:
    """Handle standard HTTP exceptions."""
    logger.error(f"HTTPException: {error}", exc_info=False)
    return create_error_response(error.description, error.code) # type: ignore


def handle_generic_exception(error: Exception) -> Response:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {error}", exc_info=True)
    return create_error_response("Internal server error", 500)


def register_middlewares(app: Flask) -> None:
    """Register middlewares and error handlers with the Flask application."""
    app.before_request(log_request_start)
    app.before_request(add_request_id)
    app.after_request(log_request_end)
    app.register_error_handler(HTTPException, handle_http_exception)
    app.register_error_handler(APIException, handle_api_exception)
    app.register_error_handler(Exception, handle_generic_exception)