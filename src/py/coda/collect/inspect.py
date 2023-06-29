from typing import Any, Iterator, Optional
from importlib import import_module
from pathlib import Path
from inspect import ismodule, isclass, ismethod, isfunction
from ..model import Symbol, SymbolType


class Introspector:
    def __init__(self):
        self.symbols: dict[str, Symbol] = {}

    def register(self, symbol: Symbol) -> Symbol:
        self.symbols[symbol.qualname] = symbol
        return symbol

    def process(self, value: Any, scope: Optional[str] = None) -> Symbol:
        if ismodule(value):
            return self.onModule(value, scope=scope)
        # elif isclass(value):
        #     return self.onClass(value, scope=scope)
        elif ismethod(value):
            return self.onFunction(value, scope=scope)
        elif isfunction(value):
            return self.onFunction(value, scope=scope)
        else:
            return self.onValue(value, scope=scope)

    def onModule(self, value: Any, scope: Optional[str] = None) -> Symbol:
        qualname = f"{scope}.{value.__name__}" if scope else value.__name__
        symbol: Symbol = Symbol(qualname, SymbolType.Module, parent=scope)
        for slot in value.__dict__:
            if child := getattr(value, slot):
                symbol.slots[slot] = self.process(child, scope=qualname).qualname

        return self.register(symbol)

    # def onClass(self, value: Any, scope: Optional[str] = None) -> Iterator[Symbol]:
    #     name = value.__name__
    #     qualname = f"{scope}.{name}" if scope else name
    #     symbol: Symbol = Symbol(qualname, SymbolType.Class)
    #     for slot in value.__dict__:
    #         if child := getattr(value, slot):
    #             yield from self.process(child, scope=qualname)
    #             symbol.slots[slot] = f"{qualname}.{slot}"
    #     yield symbol

    # def onMethod(self, value: Any, scope: Optional[str] = None) -> Iterator[Symbol]:
    #     name = value.__name__
    #     qualname = f"{scope}.{name}" if scope else name
    #     yield Symbol(qualname, SymbolType.Function, scope=scope)

    def onFunction(self, value: Any, scope: Optional[str] = None) -> Symbol:
        name = value.__name__
        return Symbol(name, SymbolType.Function, parent=scope)

    def onValue(self, value: Any, scope: Optional[str] = None) -> Symbol:
        return Symbol("#value", SymbolType.Value, parent=scope)


def module(name: str, recurse: bool = True) -> Iterator[Symbol]:
    value = import_module(name)
    introspector = Introspector()
    yield introspector.onModule(value, scope=".".join(name.split(".")[0:-1]))
    path = Path(value.__file__).absolute() if hasattr(value, "__file__") else None
    if path and path.name == "__init__.py" and not name.endswith("__"):
        for child in (
            (
                str(_.relative_to(path.parent)).rsplit(".", 1)[0]
                for _ in path.parent.glob("*.py")
            )
            if path
            else ()
        ):
            return module(f"{name}.{child}")


from ..utils.json import asJSON

if __name__ == "__main__":
    for _ in module("basekit"):
        print(asJSON(_))
# EOF
