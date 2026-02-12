import math

from fastapi import Query
from sqlalchemy.orm import Query as SAQuery


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.per_page = per_page

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


def paginate(query: SAQuery, params: PaginationParams) -> dict:
    total = query.count()
    items = query.offset(params.offset).limit(params.per_page).all()
    return {
        "data": items,
        "pagination": {
            "page": params.page,
            "per_page": params.per_page,
            "total": total,
            "pages": math.ceil(total / params.per_page) if total > 0 else 0,
        },
    }
