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

    def module(self, name: str) -> Symbol:
        module = import_module(name)
        return self.onModule(module, introspect=True)

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

    def onModule(
        self, value: Any, scope: Optional[str] = None, introspect: bool = False
    ) -> Symbol:
        qualname = f"{scope}.{value.__name__}" if scope else value.__name__
        symbol: Symbol = Symbol(qualname, SymbolType.Module, parent=scope)
        if introspect:
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
        return self.register(Symbol(name, SymbolType.Function, parent=scope))

    def onValue(self, value: Any, scope: Optional[str] = None) -> Symbol:
        return self.register(Symbol("#value", SymbolType.Value, parent=scope))


def submodules(name: str) -> Iterator[str]:
    """List the submodules of the given module, including the module itself"""
    module = None
    try:
        module = import_module(name)
    except Exception as e:
        pass
    if module:
        path = Path(module.__file__)
        base = path.parent if path.name == "__init__.py" else path
        yield name
        if base.is_dir():
            for item in base.iterdir():
                if (
                    item.is_file()
                    and item.name.endswith(".py")
                    and not item.name.startswith("__")
                ):
                    child_name = item.name.rsplit(".", 1)[0]
                    if not child_name.startswith("__"):
                        yield from submodules(f"{name}.{child_name}")
                elif item.is_dir() and (item / "__init__.py").exists():
                    yield from submodules(f"{name}.{item.name}")


from ..utils.json import asJSON

if __name__ == "__main__":
    print("=== Listing modules")
    introspector = Introspector()
    for _ in submodules("coda"):
        introspector.module(_)
    for _ in introspector.symbols.values():
        print(_.qualname)
    #     # print(asJSON(_))
# EOF
