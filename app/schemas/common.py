import math
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int      # total rows matching the filters (not just this page)
    page: int
    size: int
    pages: int      # total number of pages


def build_page(items: list, total: int, page: int, size: int) -> dict:
    pages = math.ceil(total / size) if total else 0
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail