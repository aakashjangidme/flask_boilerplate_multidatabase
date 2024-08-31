import logging
from typing import Optional, Type

from app.database.meta.connector import DatabaseConnector
from app.database.postgres_connector import PostgresConnector


# from database.oracle_connector import OracleConnector  # Assuming this is implemented

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, config: dict):
        logger.debug("Initializing DatabaseManager")
        self.config = config
        self._postgres: Optional[PostgresConnector] = None
        self._oracle: Optional[DatabaseConnector] = None

    @property
    def postgres(self) -> Optional[PostgresConnector]:
        if self._postgres is None:
            logger.debug("Lazy initializing PostgresConnector")
            self._postgres = PostgresConnector(
                user=self.config["POSTGRES_DB_USER"],
                password=self.config["POSTGRES_DB_PASSWORD"],
                host=self.config["POSTGRES_DB_HOST"],
                port=self.config["POSTGRES_DB_PORT"],
                database=self.config["POSTGRES_DB_NAME"],
            )
            self._postgres.connect()
        return self._postgres

    @property
    def oracle(self) -> Optional[DatabaseConnector]:
        if self._oracle is None:
            logger.debug("Lazy initializing OracleConnector")
            # Example connection setup; replace with actual Oracle connector details
            self._oracle = PostgresConnector(
                user=self.config["ORACLE_DB_USER"],
                password=self.config["ORACLE_DB_PASSWORD"],
                host=self.config["ORACLE_DB_HOST"],
                port=self.config["ORACLE_DB_PORT"],
                database=self.config["ORACLE_DB_NAME"],
            )
            self._oracle.connect()
        return self._oracle

    def close_connections(self) -> None:
        if self._postgres:
            self._postgres.close()
        if self._oracle:
            self._oracle.close()
