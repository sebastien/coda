from typing import Iterable, Iterator, NamedTuple
import re
from ..model import Fragment


RE_CODA_START = re.compile(r"^(?P<space>[ \t]*)#[ \t]?--+([ \t]*(?P<meta>.*))?$")
RE_CODA_COMMENT = re.compile(r"^(?P<space>[ \t]*)#(?P<content>.*)$")


class Block(NamedTuple):
    fragment: Fragment


class Line(NamedTuple):
    number: int
    offset: int
    text: str
    path: str | None = None


class TextLine(NamedTuple):
    line: Line


class CodaLine(NamedTuple):
    line: Line
    meta: str | None = None


BlockLine = CodaLine | TextLine


class BlockParser:

    @staticmethod
    def Lines(
        lines: Iterable[str], *, path: str | None = None, eol: bool = True
    ) -> Iterator[Line]:
        o: int = 0
        for i, line in enumerate(lines):
            if not eol:
                line += "\n"
            yield Line(i, o, line, path)
            o += len(line)

    @staticmethod
    def BlockLines(lines: Iterator[Line]) -> Iterator[BlockLine]:
        while line := next(lines, None):
            if line is None:
                break
            if match := RE_CODA_START.match(line.text):
                space = match.group("space")
                yield CodaLine(line, match.group("meta"))
                while (
                    (line := next(lines, None))
                    and (match := RE_CODA_COMMENT.match(line.text))
                    and match.group("space") == space
                ):
                    yield CodaLine(line)
                else:
                    if line is not None:
                        yield TextLine(line)
            else:
                yield TextLine(line)

    @staticmethod
    def Blocks(lines: Iterator[BlockLine]) -> Iterator[Block]:
        first: BlockLine | None = None
        last: BlockLine | None = None
        # Assumptions:
        # - lines are in a sequential order
        # - all lines from a file come together in a consecutive way
        for line in lines:
            if last and (
                not isinstance(line, first.__class__)
                or not line.line.path == last.line.path
            ):
                if first and last:
                    yield Block(
                        Fragment(
                            path=first.line.path,
                            offset=first.line.offset,
                            length=last.line.offset
                            + len(last.line.text)
                            - first.line.offset,
                            line=first.line.number,
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
                    path=first.line.path,
                    offset=first.line.offset,
                    length=last.line.offset - first.line.offset + len(last.line.text),
                    line=first.line.number,
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
                BlockParser.BlockLines(BlockParser.Lines(f.readlines(), path=path))
            ):
                print("<<<")
                for line in (b.fragment.read() or "").split("\n"):
                    print(i, line)
                    i += 1

# EOF
