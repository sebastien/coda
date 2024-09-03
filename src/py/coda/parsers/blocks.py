from typing import Iterator, NamedTuple
import re
from ..model import Fragment


RE_CODA_START = re.compile(r"^(?P<space>[ \t]*)#[ \t]?--+([ \t]*(?P<meta>.*))?$")
RE_CODA_COMMENT = re.compile(r"^(?P<space>[ \t]*)#(?P<content>.*)$")


class TextLine(NamedTuple):
    path: str
    offset: int
    line: int
    text: str


class CodaLine(NamedTuple):
    path: str
    offset: int
    line: int
    text: str
    meta: str | None = None


Line = CodaLine | TextLine


class Block(NamedTuple):
    fragment: Fragment


class BlockParser:

    @staticmethod
    def Lines(lines: Iterator[str], path: str) -> Iterator[Line]:
        i: int = 0
        o: int = 0
        while line := next(lines, None):
            if line is None:
                break
            if match := RE_CODA_START.match(line):
                space = match.group("space")
                yield CodaLine(path, o, i, line, match.group("meta"))
                while (
                    (line := next(lines, None))
                    and (match := RE_CODA_COMMENT.match(line))
                    and match.group("space") == space
                ):
                    yield CodaLine(path, o, i, line)
                else:
                    if line is not None:
                        yield TextLine(path, o, i, line)
            else:
                yield TextLine(path, o, i, line)
            i += 1
            o += len(line) if line is not None else 0

    @staticmethod
    def Blocks(lines: Iterator[Line]) -> Iterator[Block]:
        first: Line | None = None
        last: Line | None = None
        path: str | None = None
        # Assumptions:
        # - lines are in a sequential order
        # - all lines from a file come together in a consecutive way
        for line in lines:
            if last and (
                not isinstance(last, first.__class__) or not last.path == line.path
            ):
                if first and last:
                    yield Block(
                        Fragment(
                            path=first.path,
                            offset=first.offset,
                            length=last.offset + len(last.text) - first.offset,
                            line=first.line,
                            column=0,
                        ),
                        # TODO: Meta
                    )
                first = None
            if first is None:
                first = line
                last = line
            else:
                last = line
        if first and last:
            yield Block(
                Fragment(
                    path=first.path,
                    offset=first.offset,
                    length=last.offset - first.offset + len(last.text),
                    line=first.line,
                    column=0,
                ),
                # TODO: Meta
            )


# TODO: Given a code block, find the symbols defined
if __name__ == "__main__":
    import sys

    for path in sys.argv[1:]:
        i = 0
        with open(path) as f:
            for b in BlockParser.Blocks(
                BlockParser.Lines((_ for _ in f.readlines()), path=path)
            ):
                print("<<<")
                for line in b.fragment.read().split("\n"):
                    print(i, line)
                    i += 1

# EOF
