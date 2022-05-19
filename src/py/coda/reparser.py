import re
from typing import Optional, Union, Any, NamedTuple, Iterator
from enum import Enum

# --
# # Parsing With Regular Expressions
#
#
# This is a port from this [Observable notebook](https://observablehq.com/d/5494513845862484),
# which presents a simple way to create parsers using regular expressions.


def text(value: str) -> str:
    """Escapes the given text so that it can be used in a regepx"""
    return re.escape(value)


def seq(*expr: str) -> str:
    """Creates a sequence based on the given expresions."""
    return "".join(expr)


def _or(*expr: str) -> str:
    return f"({'|'.join(expr)})"


def opt(*expr: str) -> str:
    return f"({''.join(expr)})?"


# --
# ## Terminal Primitives


def capture(
    element: str, group: str = "item", start: Optional[Union[str, int]] = None
) -> str:
    suffix = "" if start is None else f"_{start}"
    content = element if group == "item" else recapture(element, group)
    return f"(?P<{group}{suffix}>{content})"


def recapture(element: str, name: str, group: str = "item", suffix: str = "_") -> str:
    return element.replace(f"?P<{group}{suffix}", f"?P<{name}{suffix}")


def subcapture(element: str, group: str = "item") -> str:
    return element.replace("?P<", f"?P<{group}_")


def after(element: str, sep: str = ",", group: str = "item", start: int = 0) -> str:
    return f"{sep}{capture(element, group, start)}"


def _list(
    element: str, sep: str = ",", group: str = "item", start: int = 0, max: int = 16
) -> str:
    items: list[str] = []
    for i in range(max):
        item: str = subcapture(element, f"{group}_{i}")
        items.append(
            capture(item, group, i) if i == 0 else opt(after(item, sep, group, i))
        )
    return "".join(items)


# --
# ## Useful tokens

STRING_DQ = r'"([^"]|\")+"'
STRING_SQ = r"'([^']|\')+'"
STRING_RAW = r"[^ \t]+"
NOT_SPACE = r"[^ \t]+"
STRING = _or(STRING_SQ, STRING_DQ, STRING_RAW)

# --
# ## Parsing functions


def parse(
    text: str, expr: Union[re.Pattern[str], str], raw: bool = False
) -> Optional[Union[re.Match[str], dict[str, Any]]]:
    regexp: re.Pattern[str] = (
        expr if isinstance(expr, re.Pattern) else re.compile(expr, re.MULTILINE)
    )
    res: Optional[re.Match[str]] = regexp.match(text)
    return None if res is None else res if raw else makematch(res)


def showparse(
    text: str, expr: str
) -> tuple[str, Optional[Union[re.Match[str], dict[str, Any]]]]:
    return (expr, parse(text, expr, True))


def makematch(matched: re.Match[str]) -> dict[str, Any]:
    """Transforms a match into a nested data structure"""
    res: dict[str, Any] = {}
    for k, v in matched.groupdict().items():
        if v is not None:
            res = nest(k, v, res)
    return res


def nest(
    path: Union[list[str], str], value: str, scope: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """This will nest the given `value` in the given scope at the given path"""
    res: dict[str, Any] = {} if scope is None else scope
    p: list[str] = path if isinstance(path, list) else path.split("_")
    n: int = len(p)
    current = res
    for i in range(n):
        k = p[i]
        if i == n - 1:
            current[k] = value
        else:
            v = current[k] if k in current else {}
            current[k] = v if isinstance(v, dict) else {}
            current = current[k]
    return res


assert nest("item_0_name", "John", {})
assert (
    parse(
        "f(A,B,C,D)",
        seq(
            capture("[a-z]+", "name"),
            text("("),
            capture(_list("[A-Z]+", ","), "args"),
            text(")"),
        ),
    )
) == {"name": "f", "args": {"0": "A", "1": "B", "2": "C", "3": "D"}}


# --
# ## Structure Parsing
#
# This is the adaptation of the [second notebook](https://observablehq.com/d/abab7a46ac6717b1)
# on parsing with regular expressions. We use a little bit more of Python's
# typing primitives.


class MarkerEvent(Enum):
    Start = "+"
    End = "-"
    Content = "="
    EOS = "."


class Marker(NamedTuple):
    text: str
    type: str
    event: MarkerEvent
    start: int
    end: Optional[int] = None


class Block(NamedTuple):
    start: str
    end: str


class Grammar(NamedTuple):
    sequence: dict[str, str]
    blocks: dict[str, Block]


def marks(text: str, grammar: Union[re.Pattern[str], Grammar]) -> list[Marker]:
    return [_ for _ in iterMarks(text, grammar)]


def iterMarks(grammar: Union[re.Pattern[str], Grammar], text: str) -> Iterator[Marker]:
    parser: re.Pattern[str] = (
        grammar if isinstance(grammar, re.Pattern) else compileGrammar(grammar)
    )
    offset: int = 0
    # We iterate on the input `text` using the markers regular expression.
    for matched in parser.finditer(text):
        # Wet the first non empty named group that we can find. If it
        # starts with `STA_` it's a start block, if it starts with `END_` it's an
        # end block.
        if offset != (start := matched.start()):
            yield (
                Marker(text[offset:start], "#text", MarkerEvent.Content, offset, start)
            )
        for k, m in matched.groupdict().items():
            if m is None:
                continue
            mark: str = k
            if k.startswith("STA_"):
                event = MarkerEvent.Start
            elif k.startswith("END_"):
                event = MarkerEvent.End
            else:
                event = MarkerEvent.Content
            yield Marker(m, mark, event, start, start + len(m))
            # We've found a match, so we can break the loop
            break
        offset = matched.end()
    yield Marker(text[offset:], "#eos", MarkerEvent.EOS, offset, len(text))


def compileGrammar(grammar: Grammar) -> re.Pattern[str]:
    """Returns a regular expression that corresponds to the compilation of the
    given grammar."""
    res: list[str] = [capture(v, k) for k, v in grammar.sequence.items()]
    for k, block in grammar.blocks.items():
        res.append(capture(block.start, f"STA_{k}"))
        res.append(capture(block.end, f"END_{k}"))
    return re.compile("|".join(res), re.MULTILINE)


# print(
#     compileGrammar(
#         Grammar({"statement": text(";")}, {"block": Block(text("{"), text("}"))})
#     )
# )

# --
# ## Structure Querying


# EOF
