import logging
from typing import Dict, Any
from app.models import BaseRequest, BaseResponse
from app import db
from app.utils.api_blueprint import APIBlueprint

logger = logging.getLogger(__name__)


# Example usage
api = APIBlueprint("api", __name__)


@api.register_route("/", methods=["GET"], response_model=BaseResponse)
def index(request: BaseRequest) -> Dict[str, Any]:
    logger.debug(f"Handling request: {request}")
    response_postgres, response_oracle = None, None
    if db.postgres:
        response_postgres = db.postgres.fetch_one(
            "SELECT session_user, current_database()"
        )

    if db.oracle:
        response_oracle = db.oracle.fetch_one("SELECT session_user, current_database()")

    return dict(
        message="Success",
        data=dict(postgres=response_postgres, oracle=response_oracle, health="UP"),
    )
