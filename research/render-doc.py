from typing import Iterator
from coda.utils.htmpl import html, H
from coda.collect.inspect import module
from coda.model import Symbol


def walk(symbol: Symbol) -> Iterator[Symbol]:
    yield Symbol
    yield from symbol.slots.values()


for m in module("coda"):
    for sym in walk(m):
        print(sym.qualname)

# EOF
