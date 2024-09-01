import logging
from flask import Blueprint, jsonify
from typing import Callable, Any
from app.models import BaseRequest, BaseResponse
from app.exceptions import APIException
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class APIBlueprint(Blueprint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def register_route(
        self,
        route: str,
        methods: list,
        request_model: Callable[[], BaseRequest] | None = None,
        response_model: Callable[[Any], BaseResponse] | None = None,
    ):
        """Register a route with custom request and response handling."""

        def decorator(func):
            def wrapped_func(*args, **kwargs):
                # Initialize the request model
                custom_request = None
                if request_model:
                    try:
                        custom_request = request_model()
                    except ValidationError as e:
                        logger.error(f"Request validation error: {e}")
                        raise APIException(400, "Invalid request data")
                    except Exception as e:
                        logger.error(f"Request parsing error: {e}")
                        raise APIException(400, "Invalid request")

                # Inject the custom request into the view function
                try:
                    result = func(custom_request, *args, **kwargs)
                except APIException as e:
                    logger.error(f"APIException: {e.message}")
                    return jsonify(e.to_dict()), e.status_code
                except Exception as e:
                    logger.error(f"Error during request handling: {e}")
                    raise APIException(500, "Internal server error")

                # Handle response creation
                if isinstance(result, tuple):
                    result_data, status_code = result
                else:
                    result_data = result
                    status_code = 200

                # Ensure response data is serializable
                if response_model:
                    try:
                        custom_response = response_model(**result_data)
                    except TypeError as e:
                        logger.error(f"Response serialization error: {e}")
                        raise APIException(500, "Internal server error")
                else:
                    custom_response = BaseResponse(message="Success", data=result_data)

                try:
                    response_data = custom_response.__dict__
                except Exception as e:
                    logger.error(f"Response conversion error: {e}")
                    raise APIException(500, "Internal server error")

                return jsonify(response_data), status_code

            return self.route(route, methods=methods)(wrapped_func)

        return decorator
