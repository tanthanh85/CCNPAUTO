"""Deterministic client-side pagination for an in-memory result set."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Generic, Iterator, Sequence, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class Page(Generic[T]):
    number: int
    total_pages: int
    page_size: int
    total_items: int
    items: Sequence[T]

    @property
    def has_next(self) -> bool:
        return self.number < self.total_pages


def paginate(items: Sequence[T], page_size: int) -> Iterator[Page[T]]:
    if page_size <= 0:
        raise ValueError("page_size must be greater than zero")
    total_items = len(items)
    total_pages = ceil(total_items / page_size) if total_items else 0
    for start in range(0, total_items, page_size):
        yield Page(
            number=(start // page_size) + 1,
            total_pages=total_pages,
            page_size=page_size,
            total_items=total_items,
            items=items[start : start + page_size],
        )
