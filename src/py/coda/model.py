from typing import Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# --
# # Data Model
#
# Coda primarily manages blocks of texts that contain symbols. Symbols
# denote important elements, such as function definitions, classes or types
# for code, or terms, links and definitions for code.
#
# Symbols form a tree of names.


class SymbolType(Enum):
    # These are the different parts of the program
    Program = "program"
    Module = "module"
    Function = "function"
    Class = "object"
    Object = "object"
    Slot = "slot"


# TODO: Not sure if we should have a scope type
# class ScopeType(Enum):
#     # This is to denote the declaration and definition
#     Declaration = "declaration"
#     Definition = "definition"


# --
# Fragments are use to mark subsets of the source text.
@dataclass
class Fragment:
    source: str
    start: int
    end: int


# --
# Blocks denote regions of the source text, typically comments, classes
# definitions, etc.
@dataclass
class Block:
    type: str
    fragment: Fragment


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


@dataclass
class Scope(Symbol):
    children: list[Symbol] = field(default_factory=list)


# EOF
