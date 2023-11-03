# --
# # Nota Parser
#
# I know this one is going to be big, it's the parsing of Nota, a Markdown derived
# format designed for semantic note taking.

import re
from typing import Optional, NamedTuple, Iterator, Generic, TypeVar
from contextlib import contextmanager
import inspect

K = TypeVar("K")
V = TypeVar("V")


class Collection(Generic[K, V], dict[K, V]):
    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value


@contextmanager
def declared():
    items: Collection[str, Any] = Collection()
    scope = inspect.currentframe().f_back.f_back
    l = {} | scope.f_locals
    yield items
    for k, v in scope.f_locals.items():
        if v is not l.get(k) and v is not items:
            items[k] = v


# --
# ## Parsing primitivives


class Dual(NamedTuple):
    name: str
    start: str
    end: str


# --
# # Model


class Inline(NamedTuple):
    start: re.Pattern[str]
    end: Optional[re.Pattern[str]]


class Prefix(NamedTuple):
    text: re.Pattern[str]


class Line(NamedTuple):
    start: Prefix


class Block(NamedTuple):
    start: Prefix
    end: Optional[Prefix] = None


class Grammar(NamedTuple):
    blocks: dict[str, Block]
    lines: dict[str, Line]
    inlines: dict[str, Inline]


def inline(start: str | re.Pattern[str], end: Optional[str | re.Pattern[str]] = None):
    return Inline(
        start=re.compile(re.escape(start)) if isinstance(start, str) else start,
        end=re.compile(re.escape(end)) if isinstance(end, str) else end,
    )


def prefix(start: Optional[str] = None, indented: bool = False):
    return Prefix(
        re.compile(
            (f"^(?P<indent>[ \\t]*){start}" if indented else f"^{start}")
            if start
            else r"^[ \t]*$"
        )
    )


def grammar(
    blocks: dict[str, Block], lines: dict[str, Line], inlines: dict[str, Inline]
) -> Grammar:
    return Grammar(blocks, lines, inlines)


# Grammar

# Here we want to match anything like `_*`code`*_`
with declared() as Inlines:
    Strong = inline("**")
    Emphasis = inline("*")
    Term = inline("_")
    Code = inline("`")
    Quote = inline("<<", ">>")
    Link = inline("[", re.compile(r"\)\[(?P<target>[^\]]*)\]"))
    Anchor = inline("[", "]")

with declared() as Microformats:
    Tag = inline(re.compile(r"#(?P<name>[\w\d\-_]+)"))
    Ref = inline(re.compile(r"#{(?P<name>[^}]+)}"))
    Email = inline(re.compile(r"\<(?P<email>[\w.\-_]+@[\w.\-_]+)\>"))
    URL = inline(re.compile(r"\<(?P<url>[A-z]+://[^\>]+)\>"))

# TODO: Microformats
# TODO: #URLs
# TODO: #TAG
# TODO: #{Reference}
# TODO: ISO DATE


with declared() as Prefixes:
    TodoItem = prefix(r"-[ ]*\[(?P<state>[ xX])\][ ]*", indented=True)
    OrderedListItem = prefix(r"(?P<number>[0-9a-zA-Z])[\)\.][ ]*", indented=True)
    UnorderedListItem = prefix("(?P<bullet>[-*])[ ]*", indented=True)
    DefinitionItem = prefix(r"-[ ]*(?P<term>([^:]|:[^:])+)::[ ]*$", indented=True)
    Fence = prefix(r"```(\s(?P<lang>.+))*$")
    Meta = prefix("--")
    Title = prefix("==+")
    Comment = prefix("# --")
    Heading = prefix("#+")
    Empty = prefix()


with declared() as Lines:
    Title = Line(Prefixes.Title)
    Heading = Line(Prefixes.Heading)
    Meta = Line(Prefixes.Meta)
    Comment = Line(Prefixes.Comment)

with declared() as Blocks:
    Code = Block(
        start=Fence,
        end=Fence,
    )
    TodoList = Block(
        start=Prefixes.TodoItem,
    )
    OrderedList = Block(
        start=Prefixes.OrderedListItem,
    )
    UnorderdedList = Block(
        start=Prefixes.UnorderedListItem,
    )


# This is an implicit end block, ie the next matching block will
# take over
# UnorderedListItem = Block(start=(Indent, "-"))


Nota = grammar(Blocks, Lines, Inlines)


class MatchedBlock(NamedTuple):
    name: str
    block: Optional[Block | Line]
    lines: list[str]
    start: Optional[re.Match[str]] = None
    end: Optional[re.Match[str]] = None


def parseInlines(
    line: str,
    inlines: dict[str, Inline] = Microformats | Inlines,
    *,
    start: int = 0,
    end: Optional[int] = None,
):
    o: int = start
    n: int = end or len(line)
    while o < n:
        i: int = n
        # We iterate on the active parsers
        starts: dict[str, re.Match[str]] = {}
        ends: dict[str, re.Match[str]] = {}
        for k, v in inlines.items():
            if v.end and (m := v.start.search(line, o)):
                # This expects an end
                starts[k] = m
                if (e := v.end.search(line, m.end())) and (e and e.end() <= n):
                    # If we've found the end then we register the end
                    ends[k] = e
                else:
                    # No end match, the parser becomes inactive
                    pass
        closest: Optional[str] = None
        for k, e in ends.items():
            if (j := starts[k].start()) < i:
                closest = k
                i = j
        if closest:
            yield [
                closest,
                list(
                    parseInlines(
                        line, inlines, start=starts[k].end(), end=ends[closest].start()
                    )
                ),
            ]
            o = ends[closest].end() + 1
        else:
            yield line[start:n]
            o = n + 1


def parseBlocks(
    input: Iterator[str],
    blocks: dict[str, Block | Line] = Lines | Blocks,
) -> Iterator[MatchedBlock]:
    """Takes a stream of lines and outputs matched blocks as they are parsed."""
    cur: Optional[MatchedBlock] = None
    for line in input:
        if cur and cur.block and isinstance(cur.block, Block) and cur.block.end:
            # The current block is an explicit block, so we end the block
            # when the end matches.
            if m := cur.block.end.text.match(line):
                # TODO: Maybe we should post-process the block
                cur.lines.append(line)
                yield cur._replace(end=m)
                cur = None
            else:
                cur.lines.append(line)
        else:
            matched: Optional[MatchedBlock] = None
            # Note that here the order of blocks matters, the first match
            # will take precedence over the other one.
            for k, b in blocks.items():
                if m := b.start.text.match(line):
                    if cur:
                        yield cur
                    matched = MatchedBlock(k, b, [line], m)
                    if isinstance(b, Block):
                        cur = matched
                    else:
                        yield matched
                        cur = None
                    break
            # If we haven't found a matched block, then we either create
            # a new text block or append to the current one.
            if not matched:
                if not cur or cur.name != "":
                    if cur:
                        yield cur
                    cur = MatchedBlock("", None, [line])
                else:
                    cur.lines.append(line)
    if cur:
        yield cur


def trimlines(
    lines: list[str], empty: re.Pattern[str] = re.compile("^[ \t]*$")
) -> list[str]:
    """Trim start and endint lines that are empty."""
    while lines and empty.match(lines[0]):
        lines.pop(0)
    while lines and empty.match(lines[-1]):
        lines.pop()
    return lines


EOL = "\n"


def parseLines(input: Iterator[str]):
    for b in parseBlocks(input):
        for _ in parseInlines("".join(b.lines)):
            yield _
        # if b.name:
        #     if isinstance(b.block, Block):
        #         yield (
        #             f"<{b.name}>{''.join(b.lines)[len(b.start.group()) if b.start else 0:(0 - len(b.end.group()) if b.end else None)].strip(EOL)}</{b.name}>"
        #         )
        #     elif isinstance(b.block, Line):
        #         yield f"<{b.name}>{''.join(b.lines)[len(b.start.group()) if b.start else 0:].strip()}</{b.name}>"
        # else:
        #     yield f"<p>{''.join(trimlines(b.lines))}</p>"


# --
# ## Parsing passes
import sys

for arg in sys.argv[1:] or ("pouet.txt",):
    with open(arg) as f:
        for _ in parseLines(f.readlines()):
            print(_)

# EOF
