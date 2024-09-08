import logging
from contextlib import contextmanager
from typing import Optional

import psycopg2
import psycopg2.pool
from psycopg2.extensions import connection as _Connection, cursor as _Cursor

from app.database.meta.connector import (
    DatabaseConnector,
    PagedRecordSet,
    Query,
    QueryParams,
    RecordSet,
    Record,
    RowFactory,
)
from app.models import MetaModel, PaginatedResponse, PaginationMeta
from app.utils.logger_ext.logging_decorator import log_method_call


logger = logging.getLogger(__name__)


class PostgresConnector(DatabaseConnector):
    """
    PostgreSQL connector implementation using psycopg2.

    This class manages a connection pool to a PostgreSQL database and provides
    methods to connect, close the connection, execute queries, and fetch results.
    """

    def __init__(self, user: str, password: str, host: str, port: int, database: str):
        """
        Initializes the PostgresConnector with connection details.

        :param user: Database username.
        :param password: Database password.
        :param host: Database host.
        :param port: Database port.
        :param database: Database name.
        """
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
        self.conn: Optional[_Connection] = None

    @log_method_call
    def connect(self) -> None:
        """
        Establishes a connection to the PostgreSQL database from the pool.

        This method acquires a connection from the pool and logs the connection status.
        """
        try:
            self.conn = self.pool.getconn()
            if self.conn:
                logger.debug("Successfully connected to PostgreSQL database")
        except psycopg2.DatabaseError as e:
            logger.error(f"Database connection error: {e}")
            raise

    def close(self) -> None:
        """
        Closes the connection to the PostgreSQL database and returns it to the pool.

        This method logs the status of the connection pool release.
        """
        if self.conn:
            try:
                self.pool.putconn(self.conn)
                self.conn = None
                logger.debug("PostgresConnector connection pool released")
            except psycopg2.DatabaseError as e:
                logger.error(f"Error closing the connection: {e}")
                raise

    @log_method_call
    def reconnect(self) -> None:
        """
        Reconnects to the PostgreSQL database.

        This method closes the current connection and establishes a new one.
        """
        self.close()
        self.connect()

    @contextmanager
    def get_cursor(self):
        """
        Context manager for obtaining a database cursor.

        This method handles the creation, commit, and rollback of transactions.
        If an exception occurs, it will log the error and rollback the transaction.
        """
        if not self.conn:
            self.connect()

        if self.conn:
            cursor: _Cursor = self.conn.cursor()

        try:
            yield cursor

        except psycopg2.DatabaseError as e:
            logger.error("DatabaseError: %s", e)

            if self.conn:
                self.conn.rollback()
            raise
        finally:

            cursor.close()

    def _row_factory(self, cursor: _Cursor) -> RowFactory:
        """
        Creates a factory function to convert rows into dictionaries.

        :param cursor: The database cursor used to fetch column descriptions.
        :return: A function that converts a tuple of row data into a dictionary with column names as keys.
        """
        if cursor.description is not None:
            columns: list[str] = [desc.name for desc in cursor.description]

        return lambda row: dict(zip(columns, row))

    def _execute_query(
        self,
        query: Query,
        params: QueryParams = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> PagedRecordSet:
        """
        Executes a SQL query with optional pagination and returns the results.

        :param query: SQL query to execute.
        :param params: Optional parameters for the SQL query.
        :param page: Optional page number for pagination.
        :param page_size: Optional number of rows per page for pagination.
        :return: A DatabaseResponseModel containing 'total' (total number of rows) and 'data' (query results as a list of dictionaries).
        """
        if params is None:
            params = ()

        if page is not None and page_size is not None:
            offset = (page - 1) * page_size
            query = f"""
                WITH t AS (
                    SELECT *, COUNT(*) OVER () AS total_count
                    FROM ({query}) AS subquery
                    LIMIT %s OFFSET %s
                )
                SELECT * FROM t
            """
            params = (*params, page_size, offset)
        else:
            query = f"""
                WITH t AS (
                    SELECT *, COUNT(*) OVER () AS total_count
                    FROM ({query}) AS subquery
                )
                SELECT * FROM t
            """

        result: PagedRecordSet = PaginatedResponse()

        with self.get_cursor() as cursor:
            try:
                cursor.execute(query, params)
                row_to_dict = self._row_factory(cursor)
                rows = cursor.fetchall()

                if rows:
                    total_ = rows[0][-1]  # Total count is in the last column
                    result.data = [row_to_dict(row) for row in rows]

                    total_pages = (
                        (total_ + page_size - 1) // page_size if page_size else 1
                    )
                    
                    metadata = MetaModel(
                        links=None, pagination=None
                    )
                    
                    metadata.pagination = PaginationMeta(
                        page=page or 1,
                        size=page_size or total_,
                        total_records=total_,
                        total_pages=total_pages,
                    )
                    
                    result.metadata = metadata

                logger.debug(
                    f"Query executed successfully, fetched {len(result.data)} rows"  # type: ignore
                )
            except psycopg2.DatabaseError as e:
                logger.error(f"Query execution error: {e}")
                raise

        return result

    @log_method_call
    def execute(self, query: Query, params: QueryParams = None) -> None:
        """
        Executes a non-query SQL command (e.g., INSERT, UPDATE, DELETE).

        :param query: SQL command to execute.
        :param params: Optional parameters for the SQL command.
        """
        if params is None:
            params = ()

        logger.info(f"Executing non-query: {query} with params: {params}")

        with self.get_cursor() as cursor:
            try:
                cursor.execute(query, params)
                logger.debug("Non-query executed successfully")
                if self.conn:
                    self.conn.commit()
            except psycopg2.DatabaseError as e:
                logger.error(f"Non-query execution error: {e}")
                if self.conn:
                    self.conn.rollback()
                raise

    @log_method_call
    def fetch_one(self, query: Query, params: QueryParams = None) -> Record | None:
        """
        Fetches a single row from the database.

        :param query: SQL query to execute.
        :param params: Optional parameters for the SQL query.
        :return: A dictionary representing the row, or None if no row is found.
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
        self, query: Query, size: int, params: QueryParams = None
    ) -> RecordSet:
        """
        Fetches a limited number of rows from the database.

        :param query: SQL query to execute.
        :param size: Number of rows to fetch.
        :param params: Optional parameters for the SQL query.
        :return: A list of dictionaries representing the rows.
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
        query: Query,
        params: QueryParams = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> PagedRecordSet:
        """
        Fetches all rows matching the query with optional pagination.

        :param query: SQL query to execute.
        :param params: Optional parameters for the SQL query.
        :param page: Optional page number for pagination.
        :param page_size: Optional number of rows per page for pagination.
        :return: A DatabaseResponseModel containing 'total' (total number of rows) and 'data' (query results as a list of dictionaries).
        """
        return self._execute_query(query, params, page, page_size)
