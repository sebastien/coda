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

    def process(
        self, value: Any, scope: Optional[str] = None, slot: Optional[str] = None
    ) -> Symbol:
        if ismodule(value):
            return self.onModule(value, scope=scope, slot=slot)
        elif isclass(value):
            return self.onClass(value, scope=scope, slot=slot)
        elif ismethod(value):
            return self.onFunction(value, scope=scope, slot=slot)
        elif isfunction(value):
            return self.onFunction(value, scope=scope, slot=slot)
        else:
            return self.onValue(value, scope=scope, slot=slot)

    # TODO: We should determine if the value is references (ie `from enum import Enum`)
    # or defined there.
    def onModule(
        self,
        value: Any,
        scope: Optional[str] = None,
        slot: Optional[str] = None,
        introspect: bool = False,
    ) -> Symbol:
        qualname = value.__name__
        names = qualname.split(".")
        parent = ".".join(names[:-1]) if len(names) > 1 else None
        name = names[-1]
        symbol: Symbol = Symbol(name, SymbolType.Module, parent=parent)
        if introspect:
            for slot, child in value.__dict__.items():
                symbol.slots[slot] = self.process(
                    child, scope=qualname, slot=slot
                ).qualname
        return self.register(symbol)

    def onClass(
        self, value: Any, scope: Optional[str] = None, slot: Optional[str] = None
    ) -> Symbol:
        name = value.__name__
        qualname = f"{scope}.{name}" if scope else name
        symbol: Symbol = Symbol(qualname, SymbolType.Class)
        for slot, child in value.__dict__.items():
            symbol.slots[slot] = self.process(child, scope=qualname, slot=slot).qualname
        return self.register(symbol)

    # def onMethod(self, value: Any, scope: Optional[str] = None) -> Iterator[Symbol]:
    #     name = value.__name__
    #     qualname = f"{scope}.{name}" if scope else name
    #     yield Symbol(qualname, SymbolType.Function, scope=scope)

    def onFunction(
        self, value: Any, scope: Optional[str] = None, slot: Optional[str] = None
    ) -> Symbol:
        name = value.__name__
        return self.register(Symbol(name, SymbolType.Function, parent=scope))

    def onValue(
        self, value: Any, scope: Optional[str] = None, slot: Optional[str] = None
    ) -> Symbol:
        return self.register(Symbol(slot or "#value", SymbolType.Value, parent=scope))

    def asDict(self):
        return self.symbols


def submodules(name: str) -> Iterator[str]:
    """List the submodules of the given module, including the module itself"""
    module = None
    try:
        # Module import can fail, and that's OK
        module = import_module(name)
    except Exception:
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
    with open("coda-api.json", "wt") as f:
        f.write(asJSON(introspector))
# EOF
