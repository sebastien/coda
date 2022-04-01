from typing import Optional, Any
from dataclasses import dataclass, field
from enum import Enum


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


@dataclass
class Fragment:
    source: str
    start: int
    end: int


@dataclass
class Symbol:
    """Represents a named symbol"""

    name: str
    type: SymbolType
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
