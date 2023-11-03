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
    start: str
    end: str


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


def inline(start: str, end: Optional[str] = None):
    return Inline(start, end or start)


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
    Emphasis = inline("*")
    Term = inline("_")
    Code = inline("`")
    Anchor = inline("[", "]")
    Link = inline("(", ")")


with declared() as Prefixes:
    TodoItem = prefix(r"-[ ]*\[(?P<state>[ xX])\]", indented=True)
    OrderedListItem = prefix(r"(?P<number>[0-9a-zA-Z])[\)\.]", indented=True)
    DefinitionItem = prefix(r"-[ ]*(?P<term>)::$", indented=True)
    UnorderedListItem = prefix("-", indented=True)
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


def parseBlocks(
    input: Iterator[str],
    blocks: dict[str, Block | Line] = Lines | Blocks,
) -> Iterator[MatchedBlock]:
    """Takes a stream of lines and outputs matched blocks as they are parsed."""
    cur: Optional[MatchedBlock] = None
    for line in input:
        if cur and cur.block and isinstance(cur.block, Block) and cur.block.end:
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
            if not matched:
                if not cur or cur.name != "":
                    if cur:
                        yield cur
                    cur = MatchedBlock("", None, [line])
                else:
                    cur.lines.append(line)
    if cur:
        yield cur


RE_EMPTY = re.compile("^[ \t]*$")


def trimlines(lines: list[str]) -> list[str]:
    while lines and RE_EMPTY.match(lines[0]):
        lines.pop(0)
    while lines and RE_EMPTY.match(lines[-1]):
        lines.pop()
    return lines


EOL = "\n"


def parseLines(input: Iterator[str]):
    for b in parseBlocks(input):
        if b.name:
            if isinstance(b.block, Block):
                yield (
                    f"<{b.name}>{''.join(b.lines)[len(b.start.group()) if b.start else 0:-(len(b.end.group())+1 if b.end else 0)].strip(EOL)}</{b.name}>"
                )
            elif isinstance(b.block, Line):
                yield f"<{b.name}>{''.join(b.lines)[len(b.start.group()) if b.start else 0:].strip()}</{b.name}>"
        else:
            yield f"<p>{''.join(trimlines(b.lines))}</p>"


# --
# ## Parsing passes
with open("pouet.txt") as f:
    for _ in parseLines(f.readlines()):
        print(_)

# EOF
