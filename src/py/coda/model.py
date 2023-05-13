from typing import NamedTuple, Optional

# --
# # Data Model


class Position(NamedTuple):
    offset: int
    line: Optional[int] = None
    column: Optional[int] = None


class Range(NamedTuple):
    start: Position
    end: Position


class Location(NamedTuple):
    path: str
    scheme: str = "file"


class Fragment(NamedTuple):
    text: str
    range: Range
    origin: Optional[Location] = None


def fragment(
    text: str,
    start: int,
    end: int,
    startLine: Optional[int] = None,
    startColumn: Optional[int] = None,
    endLine: Optional[int] = None,
    endColumn: Optional[int] = None,
) -> Fragment:
    return Fragment(
        text,
        Range(
            Position(start, startLine, startColumn),
            Position(end, endLine, endColumn),
        ),
    )


## EOF
