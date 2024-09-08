import logging
from flask import Blueprint, jsonify, request
from app import db
from app.models import ResponseModel, UserModel
from app.utils.helpers import ResponseBuilder

logger = logging.getLogger(__name__)

api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/", methods=["GET"])
def health_check():
    """Check the health of the application by querying database connections."""
    response = ResponseModel()
    postgres_info, oracle_info = None, None

    if db.postgres:
        postgres_info = db.postgres.fetch_one("SELECT session_user, current_database()")

    if db.oracle:
        oracle_info = db.oracle.fetch_one("SELECT session_user, current_database()")

    response.data = {"postgres": postgres_info, "oracle": oracle_info}
    response.message = "Application is healthy"

    return jsonify(response.model_dump()), 200


@api.route("/user", methods=["GET"])
def list_users():
    """Fetch and return a paginated list of users."""
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("size", 5, type=int)

    response = ResponseBuilder.paginate(
        query="SELECT * FROM users",
        model_cls=UserModel,
        endpoint="api.list_users",
        page=page,
        page_size=page_size,
    )

    return jsonify(response.model_dump(by_alias=True)), 200
