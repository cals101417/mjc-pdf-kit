"""Page-range parsing shared by Split, Rotate and Delete.

Accepts strings like "1-5, 8, 12-end" (1-based, inclusive). "end" and "last"
mean the final page. Whitespace is ignored. Returns ranges in the order typed.
"""

from __future__ import annotations


class RangeError(ValueError):
    """Raised with a message that can be shown to the user as-is."""


def _page_number(token: str, total: int) -> int:
    token = token.strip().lower()
    if token in ("end", "last"):
        return total
    if not token.isdigit():
        raise RangeError(f'"{token}" is not a page number.')
    number = int(token)
    if number < 1 or number > total:
        raise RangeError(f"Page {number} is out of range (this PDF has {total} pages).")
    return number


def parse_ranges(text: str, total: int) -> list[tuple[int, int]]:
    """Parse "1-3, 5, 9-end" into [(1, 3), (5, 5), (9, total)]."""
    if total < 1:
        raise RangeError("This PDF has no pages.")
    parts = [p for p in text.replace(";", ",").split(",") if p.strip()]
    if not parts:
        raise RangeError("Enter at least one page or range, e.g. 1-3, 5, 9-end.")

    ranges: list[tuple[int, int]] = []
    for part in parts:
        if "-" in part:
            left, _, right = part.partition("-")
            start = _page_number(left, total)
            end = _page_number(right, total)
            if start > end:
                raise RangeError(f'"{part.strip()}" goes backwards. Write it as {end}-{start}.')
        else:
            start = end = _page_number(part, total)
        ranges.append((start, end))
    return ranges


def pages_in(ranges: list[tuple[int, int]]) -> set[int]:
    """Flatten ranges into a set of 1-based page numbers."""
    return {n for start, end in ranges for n in range(start, end + 1)}
