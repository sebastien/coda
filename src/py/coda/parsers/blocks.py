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


class TextBlock(NamedTuple):
    fragment: Fragment
    text: str


class CodaBlock(NamedTuple):
    fragment: Fragment
    text: str


Line = CodaLine | TextLine
Block = CodaBlock | TextBlock


class BlockParser:

    @staticmethod
    def Lines(lines: Iterator[str], path: str) -> Iterator[Line]:
        i: int = 0
        o: int = 0
        while line := next(lines, None):
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
            o += len(line)

    @staticmethod
    def Blocks(lines: Iterator[Line]) -> Iterator[Block]:
        first: Line | None = None
        cur: Line | None = None
        cur_path: str | None = None
        # Assumptions:
        # - lines are in a sequential order
        # - all lines from a file come together in a consecutive way
        for line in lines:
            match line:
                case TextLine(path, offset, line, text):
                    yield "T"
                    pass
                case CodaLine(path, offset, line, text, meta):
                    yield "C"
                    pass
                case _:
                    raise NotImplementedError
            cur = line


if __name__ == "__main__":
    import sys

    for path in sys.argv[1:]:
        with open(path) as f:
            for _ in BlockParser.Blocks(
                BlockParser.Lines((_ for _ in f.readlines()), path=path)
            ):
                print(_)

# EOF
