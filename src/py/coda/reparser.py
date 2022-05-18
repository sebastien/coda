import re
from typing import Optional, Union, Any

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
# EOF
