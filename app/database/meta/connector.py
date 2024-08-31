from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, List, Callable


class DatabaseConnector(ABC):

    @abstractmethod
    def connect(self) -> None:
        """
        Establishes a connection to the database.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Closes the connection to the database.
        """
        pass

    @abstractmethod
    def execute(self, query: str, params: Optional[Tuple] = None) -> None:
        """
        Executes a non-query command (e.g., INSERT, UPDATE, DELETE).

        :param query: SQL command to execute.
        :param params: Parameters for the SQL command.
        """
        pass

    @abstractmethod
    def fetch_one(
        self, query: str, params: Optional[Tuple] = None
    ) -> Optional[Dict[str, any]]:
        """
        Fetches a single row from the database.

        :param query: SQL query to execute.
        :param params: Parameters for the SQL query.
        :return: Dictionary representing the row, or None if no row is found.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def fetch_all(
        self,
        query: str,
        params: Optional[Tuple] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Dict[str, any]:
        """
        Fetches all rows matching the query with optional pagination.

        :param query: SQL query to execute.
        :param params: Parameters for the SQL query.
        :param page: Page number for pagination.
        :param page_size: Number of rows per page for pagination.
        :return: Dictionary containing 'total' (total number of rows) and 'data' (query results as a list of dicts).
        """
        pass

    @abstractmethod
    def _row_factory(self, cursor) -> Callable[[Tuple], Dict[str, any]]:
        """
        Factory function to convert rows into dictionaries.

        :param cursor: The database cursor.
        :return: A function that converts a row into a dictionary.
        """
        pass

    @abstractmethod
    def reconnect(self) -> None:
        """
        Reconnects to the database, handling any necessary cleanup.
        """
        pass
