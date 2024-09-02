# --
# # Coda Parser
#
# This is the simplest implementation of the coda block format. Any text within a block
# starting with `<spaces>#--\n` and with next lines starting with `<spaces>#` will
# be a coda block.
from typing import Iterator, TypeVar, NamedTuple, Optional
import re

T = TypeVar("T")

EXAMPLE = """\
# --
# BLOCK:A.0
# BLOCK:A.1
# BLOCK:A.2
CODE
# COMMENT
# COMMENT
CODE
# --
# BLOCK:B.0
CODE
# COMMENT"""

CODA_START = re.compile(r"^(?P<space>[ \t]*)#[ \t]?--$")
CODA_COMMENT = re.compile(r"^(?P<space>[ \t]*)#(?P<content>.*)$")


def Lines(text: str, sep: str = "\n", withSeparator: bool = False) -> Iterator[str]:
    i: int = 0
    d: int = 0 if withSeparator else -1
    while (o := text.find(sep, i)) >= 0:
        yield text[i : (i := (o + 1)) + d]


class BlockLine(NamedTuple):
    type: str
    index: int
    text: str


def BlockLines(lines: Iterator[str]) -> Iterator[BlockLine]:
    i: int = 0
    while line := next(lines, None):
        if match := CODA_START.match(line):
            space = match.group("space")
            i += 1
            yield BlockLine("C", i, line)
            while (
                (line := next(lines, None))
                and (match := CODA_COMMENT.match(line))
                and match.group("space") == space
            ):
                yield BlockLine("C", i, line)
            else:
                i += 1
                if line is not None:
                    yield BlockLine("_", i, line)
        else:
            yield BlockLine("_", i, line)


class Block(NamedTuple):
    type: str
    text: list[str]


def Blocks(blockLines: Iterator[BlockLine]) -> Iterator[Block]:
    i: int = -1
    b: Optional[Block] = None
    for t, j, l in blockLines:
        if j == i:
            assert b
            b.text.append(l)
        else:
            if b:
                yield b
            b = Block(t, [l])
            i = j
    if b:
        yield b


if __name__ == "__main__":
    from pathlib import Path

    example = "tests/example-format.txt"
    print(f"=== TEST Parsing example: {example}")

    for atom in Blocks(BlockLines(Lines(EXAMPLE))):
        print(atom)

    print("--- EOK")
# EOF
