from typing import Iterator, Optional, NamedTuple
from dataclasses import dataclass
from pathlib import Path
import re

# --
# The idea of the combined parser is to do as follow
#
# Separate a file in blocks:
#
# - Text blocks
# - Code blocks
#
# Code blocks contain Symbol definitions and symbol references.


class Fragment(NamedTuple):
    # -- doc
    # `start` offset
    start: int
    # -- doc
    # `end` offset
    end: int


@dataclass
class Block:
    type: str
    fragment: Fragment
    lines: list[str]


# --
RE_CODA_BLOCK = re.compile(r"^[ \t]*#\s*--+([ \t]*(?P<meta>.*))?$")
RE_COMMENT = re.compile(r"^[ \t]*#(?P<content>.*)$")


# Regular comment


class BlockParser:
    @staticmethod
    def ParseLines(lines: Iterator[str]) -> Iterator[Block]:
        offset: int = 0
        block_type: Optional[str] = None
        block_start: int = 0
        block_lines: list[str] = []
        for line in lines:
            if match := RE_CODA_BLOCK.match(line):
                if block_type:
                    yield Block(block_type, Fragment(block_start, offset), block_lines)
                meta = match.group("meta").split()
                block_start = offset
                block_type = meta[0] if meta else "text"
                block_lines = [line]
            elif RE_COMMENT.match(line):
                if block_type in ("coda", "comment"):
                    block_lines.append(line)
                else:
                    if block_type:
                        yield Block(
                            block_type, Fragment(block_start, offset), block_lines
                        )
                    block_type = "comment"
                    block_start = offset
                    block_lines = [line]
            else:
                if block_type == "code":
                    block_lines.append(line)
                else:
                    if block_type:
                        yield Block(
                            block_type, Fragment(block_start, offset), block_lines
                        )
                    block_type = "code"
                    block_start = offset
                    block_lines = [line]

            offset += len(line)
        if block_type and block_lines:
            yield Block(block_type, Fragment(block_start, offset), block_lines)


class BlockFormatter:
    @staticmethod
    def HTML(blocks: Iterator[Block]):
        yield "<html><body>"
        for block in blocks:
            match block.type:
                case "comment":
                    yield "<pre style='color:green;'>"
                    yield from (_ for _ in block.lines)
                    yield "</pre>"
                case "code":
                    yield "<pre style='color:grey;'>"
                    yield from (_ for _ in block.lines)
                    yield "</pre>"
                case "coda":
                    yield "<em style='color:blue;'>"
                    yield from (_ for _ in block.lines)
                    yield "</em>"
                case _:
                    yield "<pre>"
                    yield from (_ for _ in block.lines)
                    yield "</pre>"
        yield "</body>/<html>"


if __name__ == "__main__":
    import sys

    out = sys.stdout.write
    with open(__file__, "rt") as f:
        for _ in BlockFormatter.HTML(BlockParser.ParseLines(f.readlines())):
            out(_)


# EOF
