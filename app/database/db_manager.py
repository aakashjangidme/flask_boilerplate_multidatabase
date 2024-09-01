import logging
from typing import Optional

from flask import g

from app.database.meta.connector import DatabaseConnector
from app.database.postgres_connector import PostgresConnector


logger = logging.getLogger(__name__)


class DatabaseManager:

    __ext_name__ = "db_manager"

    def __init__(self, app=None, config=None):
        self._postgres: Optional[DatabaseConnector] = None
        self._oracle: Optional[DatabaseConnector] = None

        if config is not None:
            self.config = config

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the database manager with the Flask app."""
        self.config = app.config

        app.extensions[self.__ext_name__] = self

        @app.before_request
        def setup_db():
            if self.__ext_name__ not in g:
                g.db_manager = self

        @app.teardown_appcontext
        def teardown_db(exception: Optional[Exception]) -> None:
            db_manager = g.pop(self.__ext_name__, None)
            if db_manager:
                db_manager.close_connections()

    @property
    def postgres(self) -> Optional[DatabaseConnector]:
        if self._postgres is None:
            try:
                logger.debug("Lazy initializing PostgresConnector")
                self._postgres = PostgresConnector(
                    user=self.config["POSTGRES_DB_USER"],
                    password=self.config["POSTGRES_DB_PASSWORD"],
                    host=self.config["POSTGRES_DB_HOST"],
                    port=self.config["POSTGRES_DB_PORT"],
                    database=self.config["POSTGRES_DB_NAME"],
                )
                self._postgres.connect()
            except Exception as e:
                logger.error(f"Failed to connect to Postgres: {e}")
                self._postgres = None
        return self._postgres

    @property
    def oracle(self) -> Optional[DatabaseConnector]:
        if self._oracle is None:
            try:
                logger.debug("Lazy initializing OracleConnector")
                self._oracle = PostgresConnector(
                    user=self.config["ORACLE_DB_USER"],
                    password=self.config["ORACLE_DB_PASSWORD"],
                    host=self.config["ORACLE_DB_HOST"],
                    port=self.config["ORACLE_DB_PORT"],
                    database=self.config["ORACLE_DB_NAME"],
                )
                self._oracle.connect()
            except Exception as e:
                logger.error(f"Failed to connect to Oracle: {e}")
                self._oracle = None
        return self._oracle

    def close_connections(self) -> None:
        if self._postgres:
            try:
                self._postgres.close()
            except Exception as e:
                logger.error(f"Failed to close Postgres connection: {e}")
        if self._oracle:
            try:
                self._oracle.close()
            except Exception as e:
                logger.error(f"Failed to close Oracle connection: {e}")
