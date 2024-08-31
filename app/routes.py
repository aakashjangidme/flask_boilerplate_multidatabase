import logging
from flask import Blueprint, g, jsonify
from typing import Dict, Any


logger = logging.getLogger(__name__)

api = Blueprint("api", __name__)


@api.route("/")
def index():
    db = g.db_manager
    response_postgres, response_oracle = None, None
    if db.postgres:
        response_postgres = db.postgres.fetch_one(
            "SELECT session_user, current_database()"
        )

    if db.oracle:
        response_oracle = db.oracle.fetch_one("SELECT session_user, current_database()")

    return jsonify(
        data=dict(postgres=response_postgres, oracle=response_oracle, health="UP")
    )
