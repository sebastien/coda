from .utils.reparser import Marks, Marker, marks, compile
from .utils.statemachine import StateMachine, CompletionEvent
from .utils.grammar import grammar
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
        "Block": "blockStart comment*",
        "Comment": "comment+",
        "Sep": "separator+",
        "Code": "_+",
    }
)


def blocks(text: str) -> Iterator[Block]:
    parser: StateMachine = CODA_BLOCK_GRAMMAR
    markers: list[Marker] = []

    def process(markers: list[Marker], event: CompletionEvent) -> Block:
        start = markers[event.start].start
        end = markers[event.end].start if event.end < len(markers) else markers[-1].end
        fragment = StringFragment(text, start, end)
        return Block(event.name or "#text", fragment)

    for marker in marks(text, CODA_BLOCK_MARKS):
        markers.append(marker)
        for event in parser.feed(marker.type):
            yield process(markers, event)
    if event := parser.end():
        yield process(markers, event)


if __name__ == "__main__":
    import sys

    for b in blocks(open(sys.argv[1]).read()):
        print(b)

# EOF
