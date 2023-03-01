from typing import Iterator, Optional, NamedTuple
from dataclasses import dataclass
from html import escape
import texto
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
    meta: Optional[str]
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
        block_meta: Optional[str] = None
        # NOTE: This should be refactored, it's too repetitive
        for line in lines:
            if match := RE_CODA_BLOCK.match(line):
                if block_type:
                    yield Block(
                        block_type,
                        block_meta,
                        Fragment(block_start, offset),
                        block_lines,
                    )
                block_start = offset
                block_type = "text"
                block_lines = [line]
                block_meta = match.group("meta").strip()
            elif RE_COMMENT.match(line):
                if block_type in ("text", "comment"):
                    block_lines.append(line)
                else:
                    if block_type:
                        yield Block(
                            block_type,
                            block_meta,
                            Fragment(block_start, offset),
                            block_lines,
                        )
                    block_type = "comment"
                    block_start = offset
                    block_lines = [line]
                    block_meta = None
            else:
                if block_type == "code":
                    block_lines.append(line)
                else:
                    if block_type:
                        yield Block(
                            block_type,
                            block_meta,
                            Fragment(block_start, offset),
                            block_lines,
                        )
                    block_type = "code"
                    block_start = offset
                    block_lines = [line]
                    block_meta = None

            offset += len(line)
        if block_type and block_lines:
            yield Block(
                block_type, block_meta, Fragment(block_start, offset), block_lines
            )


class BlockFormatter:
    @staticmethod
    def HTML(blocks: Iterator[Block]):
        for block in blocks:
            match block.type:
                case "comment":
                    yield f"<pre class={block.type} style='color:green;'>"
                    yield from (escape(_) for _ in block.lines)
                    yield "</pre>"
                case "code":
                    yield f"<pre class={block.type} style='color:grey;'>"
                    yield from (escape(_) for _ in block.lines)
                    yield "</pre>"
                case "text":
                    yield f"<em class={block.type} style='color:blue;'>"
                    text = "\n".join(_.strip().lstrip("# ") for _ in block.lines[1:])
                    yield texto.render(texto.parse(text))
                    yield "</em>"
                case _:
                    yield f"<pre class={block.type}>"
                    yield from (escape(_) for _ in block.lines)
                    yield "</pre>"
        yield "</body><html>"


if __name__ == "__main__":
    import sys

    out = sys.stdout.write
    with open(__file__, "rt") as f:
        for _ in BlockFormatter.HTML(BlockParser.ParseLines(f.readlines())):
            out(_)


# EOF
