from ..utils.reparser import Marks, Marker, MarkerEvent, marks, compile
from ..utils.statemachine import StateMachine, CompletionEvent
from ..utils.grammar import grammar
from ..model import Fragment, Range, Position
from typing import Iterator, Any
import re

CODA_START = re.compile(r"^(?P<space>[ \t]*)#[ \t]?--$")
CODA_COMMENT = re.compile(r"^(?P<space>[ \t]*)#(?P<content>.*)$")


CODA_BLOCK_MARKS = compile(
    Marks(
        {
            "blockStart": r"^([ \t]*)#[ ]+--[ ]*\n",
            "comment": r"^([ \t]*)#.*\n",
            "separator": r"^[ \t]*\n",
        },
        {},
    )
)
CODA_BLOCK_GRAMMAR = grammar(
    {
        "Block": "blockStart comment*",
        # "Comment": "comment+",
        # "Sep": "separator+",
        "Code": "_+",
    }
)


def blocks(text: str) -> Iterator[Any]:
    parser: StateMachine = StateMachine(CODA_BLOCK_GRAMMAR)
    markers: list[Marker] = []

    def process(markers: list[Marker], event: CompletionEvent) -> Any:
        start = (
            markers[event.start].start
            if event.start < len(markers)
            else markers[-1].start
        )
        end = markers[event.end].start if event.end < len(markers) else markers[-1].end
        fragment = Fragment(text, Range(Position(start), Position(end)))
        return (event.name or "#text", fragment)

    for marker in marks(text, CODA_BLOCK_MARKS):
        print("MARKER", marker)
        if marker.type is MarkerEvent.EOS:
            if event := parser.end():
                yield process(markers, event)
        else:
            markers.append(marker)
            for event in parser.feed(marker.type):
                yield process(markers, event)
    parser.reset()


if __name__ == "__main__":
    import sys

    for b in blocks(open(sys.argv[1]).read()):
        print(b)

# EOF
