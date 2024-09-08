import logging
from typing import Type, TypeVar
from pydantic import BaseModel
from app import db
from app.models import MetaModel, PaginatedResponse
from app.utils.pagination_handler import PaginationHandler

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class ResponseBuilder:
    @staticmethod
    def paginate(
        query: str,
        model_cls: Type[T],
        endpoint: str,
        page: int = 1,
        page_size: int = 5,
    ) -> PaginatedResponse[T]:
        """Fetch paginated data from the database and create a response model."""
        response = PaginatedResponse[T](data=[], pagination=None, links=None)

        try:
            # Check if the PostgreSQL connection is available
            if not db.postgres:
                raise ConnectionError("PostgreSQL connection is not available")

            # Fetch paginated results from the database
            result = db.postgres.fetch_all(query, page=page, page_size=page_size)

            if not result or not result.data:
                logger.warning(f"No data found for the query: {query}")
                return response

            # Populate the response data
            response.data = [model_cls(**item) for item in result.data]

            if result.metadata:

                # Generate pagination links
                total_pages = (
                    result.metadata.pagination.total_pages
                    if result.metadata.pagination
                    else 0
                )

                metadata = MetaModel(
                    pagination=result.metadata.pagination,
                    links=PaginationHandler.generate_links(
                        endpoint, page, page_size, total_pages
                    )
                )

            response.metadata = metadata

        except ConnectionError as e:
            logger.error(f"Database connection error: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"An error occurred during data retrieval: {str(e)}")
            raise

        return response
