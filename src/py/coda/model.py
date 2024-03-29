from typing import Optional, Any, NamedTuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# --
# # Data Model
#
# Coda primarily manages blocks of texts that contain symbols. Symbols
# denote important elements, such as function definitions, classes or types
# for code, or terms, links and definitions for code.
#
# Symbols form a tree of names.


# Alternative
# class Position(NamedTuple):
#     offset: int
#     line: Optional[int] = None
#     column: Optional[int] = None
#
#
# class Range(NamedTuple):
#     start: Position
#     end: Position
#
#
# class Location(NamedTuple):
#     path: str
#     scheme: str = "file"
#
#
# class Fragment(NamedTuple):
#     text: str
#     range: Range
#     origin: Optional[Location] = None
#
#
# def fragment(
#     text: str,
#     start: int,
#     end: int,
#     startLine: Optional[int] = None,
#     startColumn: Optional[int] = None,
#     endLine: Optional[int] = None,
#     endColumn: Optional[int] = None,
# ) -> Fragment:
#     return Fragment(
#         text,
#         Range(
#             Position(start, startLine, startColumn),
#             Position(end, endLine, endColumn),
#         ),
#     )


class SymbolType(Enum):
    # These are the different parts of the program
    Program = "program"
    Module = "module"
    Function = "function"
    Class = "object"
    Slot = "slot"
    Object = "object"
    Value = "value"


# TODO: Not sure if we should have a scope type
# class ScopeType(Enum):
#     # This is to denote the declaration and definition
#     Declaration = "declaration"
#     Definition = "definition"


# --
# Fragments are use to mark subsets of the source text.
class Fragment:
    @property
    def text(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}:{repr(self.text)}>"

    def __str__(self) -> str:
        return self.text


class LiteralFragment(Fragment):
    def __init__(self, text: str):
        super().__init__()
        self.value = text

    @property
    def text(self) -> str:
        return self.value


class StringFragment(Fragment):
    def __init__(self, text: str, start: int = 0, end: Optional[int] = None):
        self.source: str = text
        self.start = start
        self.end = end

    @property
    def text(self) -> str:
        return self.source[self.start : self.end]


# --
# Blocks denote regions of the source text, typically comments, classes
# definitions, etc.
@dataclass
class Block:
    type: str
    fragment: Fragment

    @property
    def text(self) -> str:
        return self.fragment.text


# --
# Symbols are extracting by parsing, for instance using TreeSitter to query
# the text.
@dataclass
class Symbol:
    """Represents a named symbol"""

    name: str
    type: SymbolType
    # Symbols are connected indirectly by reference
    parent: Optional[str] = None
    fragment: Optional[Fragment] = None
    slots: dict[str, str] = field(default_factory=dict)
    relations: dict[str, str] = field(default_factory=dict)

    @property
    def qualname(self):
        return self.name if not self.parent else f"{self.parent}.{self.name}"

    def asDict(self) -> dict:
        res = asdict(self)
        res["qualname"] = self.qualname
        return res


@dataclass
class Scope(Symbol):
    children: list[Symbol] = field(default_factory=list)


## EOF
