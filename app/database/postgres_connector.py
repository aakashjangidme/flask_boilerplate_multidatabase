import logging
import psycopg2.pool
import psycopg2
from contextlib import contextmanager
from typing import Callable, List, Dict, Tuple, Optional
from app.database.meta.connector import DatabaseConnector
from app.utils.logger_ext.logging_decorator import log_method_call



logger = logging.getLogger(__name__)


class PostgresConnector(DatabaseConnector):
    def __init__(self, user, password, host, port, database):
        self.pool: psycopg2.pool.SimpleConnectionPool = (
            psycopg2.pool.SimpleConnectionPool(
                minconn=5,
                maxconn=20,
                user=user,
                password=password,
                host=host,
                port=port,
                database=database,
            )
        )
        self.conn = None

    @log_method_call
    def connect(self):
        try:
            self.conn = self.pool.getconn()
            if self.conn:
                logger.debug("Successfully connected to PostgreSQL database")
        except psycopg2.DatabaseError as e:
            logger.error(f"Database connection error: {e}")
            raise

    def close(self):
        if self.conn:
            try:
                self.pool.putconn(self.conn)
                self.conn = None
                logger.debug("Connection closed successfully")
            except psycopg2.DatabaseError as e:
                logger.error(f"Error closing the connection: {e}")
                raise

    @log_method_call
    def reconnect(self):
        """Reconnect to the database."""
        self.close()
        self.connect()

    @contextmanager
    def get_cursor(self):
        """
        Context manager for database cursor, automatically handles exceptions
        and commits/rollbacks.
        """
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except psycopg2.DatabaseError as e:
            self.conn.rollback()
            logger.error(f"DatabaseError: {e}")
            raise
        finally:
            cursor.close()

    def _row_factory(self, cursor) -> Callable[[Tuple], Dict[str, any]]:
        """
        Factory function to convert rows into dictionaries.

        :param cursor: The database cursor.
        :return: A function that converts a row into a dictionary.
        """
        columns = [desc[0] for desc in cursor.description]
        return lambda row: dict(zip(columns, row))

    def _execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Dict[str, any]:
        """
        Executes a query with optional pagination and returns results as a dictionary.

        :param query: SQL query to execute.
        :param params: Parameters for the SQL query.
        :param page: Page number for pagination.
        :param page_size: Number of rows per page for pagination.
        :return: Dictionary containing 'total' (total number of rows) and 'data' (query results as a list of dicts).
        """
        if params is None:
            params = ()

        if page is not None and page_size is not None:
            offset = (page - 1) * page_size
            query = f"""
                WITH paginated AS (
                    SELECT *, COUNT(*) OVER () AS total_count
                    FROM ({query}) AS subquery
                    LIMIT %s OFFSET %s
                )
                SELECT * FROM paginated
            """
            params = (*params, page_size, offset)
        else:
            query = f"""
                WITH paginated AS (
                    SELECT *, COUNT(*) OVER () AS total_count
                    FROM ({query}) AS subquery
                )
                SELECT * FROM paginated
            """

        result = {"total": 0, "data": []}

        with self.get_cursor() as cursor:
            try:
                cursor.execute(query, params)
                rows = cursor.fetchall()

                if rows:
                    row_to_dict = self._row_factory(cursor)
                    result["total"] = rows[0][-1]  # Total count is in the last column
                    result["data"] = [row_to_dict(row) for row in rows]

                logger.debug(
                    f"Query executed successfully, fetched {len(result['data'])} rows"
                )
            except psycopg2.DatabaseError as e:
                logger.error(f"Query execution error: {e}")
                raise

        return result

    def execute(self, query: str, params: Optional[Tuple] = None):
        """
        Executes a non-query command (e.g., INSERT, UPDATE, DELETE).

        :param query: SQL command to execute.
        :param params: Parameters for the SQL command.
        """
        if params is None:
            params = ()
        logger.info(f"Executing non-query: {query} with params: {params}")
        with self.get_cursor() as cursor:
            try:
                cursor.execute(query, params)
                logger.debug("Non-query executed successfully")
            except psycopg2.DatabaseError as e:
                logger.error(f"Non-query execution error: {e}")
                raise

    @log_method_call
    def fetch_one(
        self, query: str, params: Optional[Tuple] = None
    ) -> Optional[Dict[str, any]]:
        """
        Fetches a single row from the database.

        :param query: SQL query to execute.
        :param params: Parameters for the SQL query.
        :return: Dictionary representing the row, or None if no row is found.
        """
        if params is None:
            params = ()
        with self.get_cursor() as cursor:
            try:
                cursor.execute(query, params)
                row = cursor.fetchone()
                if row:
                    row_to_dict = self._row_factory(cursor)
                    return row_to_dict(row)
                return None
            except psycopg2.DatabaseError as e:
                logger.error(f"Error fetching one row: {e}")
                raise

    @log_method_call
    def fetch_many(
        self, query: str, size: int, params: Optional[Tuple] = None
    ) -> List[Dict[str, any]]:
        """
        Fetches a limited number of rows from the database.

        :param query: SQL query to execute.
        :param size: Number of rows to fetch.
        :param params: Parameters for the SQL query.
        :return: List of dictionaries representing the rows.
        """
        if params is None:
            params = ()
        with self.get_cursor() as cursor:
            try:
                cursor.execute(query, params)
                rows = cursor.fetchmany(size)
                row_to_dict = self._row_factory(cursor)
                return [row_to_dict(row) for row in rows]
            except psycopg2.DatabaseError as e:
                logger.error(f"Error fetching many rows: {e}")
                raise

    @log_method_call
    def fetch_all(
        self,
        query: str,
        params: Optional[Tuple] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> List[Dict[str, any]]:
        """
        Fetches all rows matching the query.

        :param query: SQL query to execute.
        :param params: Parameters for the SQL query.
        :return: List of dictionaries representing the rows.
        """
        return self._execute_query(query, params, page, page_size)
