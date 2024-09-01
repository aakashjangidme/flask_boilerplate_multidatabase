from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple, Dict, List, Callable, TypeAlias

from app.models import  PaginatedResponse

# Type aliases

# Optional tuple of parameters to be used in SQL queries.
# This allows for parameterized queries where placeholders in the query
# are replaced with these values. Example: (1, 'example')
QueryParams: TypeAlias = Optional[Tuple[Any, ...]]

# SQL query represented as a string.
# This is used to specify the SQL command to be executed against the database.
# Example: "SELECT * FROM users WHERE id = %s"
Query: TypeAlias = str

# A single row from a query result, represented as a dictionary.
# The keys in this dictionary are column names, and the values are the data
# for each column in that row. Example: {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'}
Row: TypeAlias = Dict[str, Any]

# A factory function that converts a tuple of row data into a Row dictionary.
# This callable takes a tuple (representing a row) and returns a dictionary
# with column names as keys and row data as values. Example:
# lambda row: {'id': row[0], 'name': row[1], 'email': row[2]}
RowFactory: TypeAlias = Callable[[Tuple[Any, ...]], Row]

# Data model representing a paginated query result.
# It includes both the total number of rows and the data for the current page.
# Example: DatabaseResponseModel(total=100, data=[{'id': 1, 'name': 'Alice'}])
PagedResult: TypeAlias = PaginatedResponse

# A list of rows, where each row is a dictionary representing a single record.
# Each dictionary follows the Row type alias. Example:
# [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
Result: TypeAlias = List[Row]


class DatabaseConnector(ABC):
    """
    Abstract base class for database connectors.

    This class defines the essential methods that any concrete database connector
    implementation must provide. It includes methods for connecting, closing the
    connection, executing queries, and fetching results.
    """

    @abstractmethod
    def connect(self) -> None:
        """
        Establishes a connection to the database.

        This method should handle the connection setup and ensure that
        the connection is established successfully.
        """

    @abstractmethod
    def close(self) -> None:
        """
        Closes the connection to the database.

        This method should ensure that the connection is properly closed
        and any resources are released.
        """

    @abstractmethod
    def execute(self, query: Query, params: QueryParams = None) -> None:
        """
        Executes a non-query command (e.g., INSERT, UPDATE, DELETE).

        :param query: SQL command to execute.
        :param params: Optional parameters for the SQL command. These are used
                       to safely insert values into the query.
        """

    @abstractmethod
    def fetch_one(self, query: Query, params: QueryParams = None) -> Row:
        """
        Fetches a single row from the database.

        :param query: SQL query to execute.
        :param params: Optional parameters for the SQL query.
        :return: A dictionary representing the row, or None if no row is found.
        """

    @abstractmethod
    def fetch_many(self, query: Query, size: int, params: QueryParams = None) -> Result:
        """
        Fetches a limited number of rows from the database.

        :param query: SQL query to execute.
        :param size: Number of rows to fetch.
        :param params: Optional parameters for the SQL query.
        :return: A list of dictionaries representing the rows.
        """

    @abstractmethod
    def fetch_all(
        self,
        query: Query,
        params: QueryParams = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> PagedResult:
        """
        Fetches all rows matching the query with optional pagination.

        :param query: SQL query to execute.
        :param params: Optional parameters for the SQL query.
        :param page: Optional page number for pagination.
        :param page_size: Optional number of rows per page for pagination.
        :return: A DatabaseResponseModel containing 'total' (total number of rows)
                 and 'data' (query results as a list of dictionaries).
        """

    @abstractmethod
    def _row_factory(self, cursor) -> RowFactory:
        """
        Factory function to convert rows into dictionaries.

        :param cursor: The database cursor.
        :return: A function that converts a tuple of row data into a dictionary.
        """

    @abstractmethod
    def reconnect(self) -> None:
        """
        Reconnects to the database, handling any necessary cleanup.

        This method should ensure that the connection is properly re-established,
        especially after any disconnection or failure scenarios.
        """
