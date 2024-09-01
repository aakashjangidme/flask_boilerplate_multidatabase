import logging
from flask import Blueprint, jsonify, request, url_for
from app import db
from app.models import (
    PaginatedResponse,
    ResponseModel,
    UserModel,
    UserResponseModel,
)

logger = logging.getLogger(__name__)

api = Blueprint("api", __name__)


def create_links(endpoint: str, page: int, page_size: int, total_pages: int) -> dict:
    """Generate pagination links (self, next, prev) for a given endpoint."""
    links = {
        "self": url_for(endpoint, page=page, size=page_size, _external=True),
        "next": None,
        "prev": None,
    }

    if page < total_pages:
        links["next"] = url_for(endpoint, page=page + 1, size=page_size, _external=True)

    if page > 1:
        links["prev"] = url_for(endpoint, page=page - 1, size=page_size, _external=True)

    return links


def fetch_paginated_data(
    query: str,
    model: PaginatedResponse,
    endpoint: str,
    page: int = 1,
    page_size: int = 5,
) -> PaginatedResponse:
    """Fetch paginated data from the database and construct response model."""
    if db.postgres:
        paged_result = db.postgres.fetch_all(query, page=page, page_size=page_size)

        if paged_result.data:
            model.data = [UserModel(**user) for user in paged_result.data]
            model.pagination = paged_result.pagination
            model.links = create_links(
                endpoint, page, page_size, paged_result.pagination.total_pages  # type: ignore
            )

    return model


@api.route("/", methods=["GET"])
def index():
    response = ResponseModel()
    response_postgres, response_oracle = None, None

    if db.postgres:
        response_postgres = db.postgres.fetch_one(
            "SELECT session_user, current_database()"
        )

    if db.oracle:
        response_oracle = db.oracle.fetch_one("SELECT session_user, current_database()")

    response.data = dict(postgres=response_postgres, oracle=response_oracle)
    response.message = "Health is Up"

    return jsonify(response.model_dump()), 200


@api.route("/user", methods=["GET"])
def user():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("size", 5, type=int)

    response = fetch_paginated_data(
        query="SELECT * FROM users",
        model=UserResponseModel(),
        endpoint="api.user",
        page=page,
        page_size=page_size,
    )

    return jsonify(response.model_dump()), 200
