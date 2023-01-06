from .utils.reparser import Marks, Marker, marks, compile
from .utils.grammar import StateMachine, grammar, seq
from .model import StringFragment, Block
from typing import Iterator
import re

CODA_START = re.compile(r"^(?P<space>[ \t]*)#[ \t]?--$")
CODA_COMMENT = re.compile(r"^(?P<space>[ \t]*)#(?P<content>.*)$")


CODA_BLOCK_MARKS = compile(
    Marks(
        {
            "blockStart": r"^([ \t]*)#[ ]+--[ ]*\n",
            "comment": r"^([ \t]*)#.*$",
            "separator": r"^[ \t]*\n$",
        },
        {},
    )
)
CODA_BLOCK_GRAMMAR = grammar(
    {
        "Block": seq("blockStart", "comment*"),
        "Comment": seq("comment+"),
        "Sep": seq("separator+"),
        "Code": seq("_+"),
    }
)


def blocks(text: str) -> Iterator[Block]:
    parser = StateMachine(CODA_BLOCK_GRAMMAR, name="coda-blocks")
    markers: list[Marker] = []
    for _ in ["separator", "separator", "separator"]:
        print("_", _)
        for m in parser.feed(_):
            print("m", m)
            yield m
    if False:
        for marker in marks(text, CODA_BLOCK_MARKS):
            markers.append(marker)
            print("M", marker.type)
            for event in parser.feed(marker.type):
                start = markers[event.start].start
                end = markers[event.end].start
                fragment = StringFragment(text, start, end)
                # yield Block(event.name, fragment)
        yield None


if __name__ == "__main__":
    import sys

    for b in blocks(open(sys.argv[1]).read()):
        print(b)

# EOF
