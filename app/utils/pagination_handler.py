from flask import url_for
from app.models import LinksMeta


class PaginationHandler:
    @staticmethod
    def generate_links(
        endpoint: str, page: int, page_size: int, total_pages: int
    ) -> LinksMeta:
        """Generate pagination links for the specified endpoint."""
        links = LinksMeta()

        links.self = url_for(endpoint, page=page, size=page_size, _external=True)
        links.next = (
            url_for(endpoint, page=page + 1, size=page_size, _external=True)
            if page < total_pages
            else None
        )
        links.prev = (
            url_for(endpoint, page=page - 1, size=page_size, _external=True)
            if page > 1
            else None
        )

        return links
