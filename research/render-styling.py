# --
# # Design Tokens
#
# This notebook is about creating/writing stylesheets.
from typing import Optional, Any
from contextlib import contextmanager
import inspect


# TODO: List of CSS style properties
class Style:
    @staticmethod
    def PropertyName(name: str) -> str:
        return name

    @staticmethod
    def PropertyValue(value: str) -> str:
        return value

    def __init__(
        self, properties: Optional[dict[str, str]] = None, name: Optional[str] = None
    ):
        self.properties: dict[str, str] = (
            {
                Style.PropertyName(k): Style.PropertyValue(v)
                for k, v in properties.items()
            }
            if properties
            else {}
        )
        self.name: Optional[str] = name

    def derive(self, selector, **properties: str) -> "Style":
        return self


def style(**properties: str):
    return Style(properties)


@contextmanager
def styles():
    stylesheet: list[Style] = []
    try:
        yield stylesheet
    finally:
        for k, v in (inspect.currentframe().f_back.f_back.f_locals).items():
            if isinstance(v, Style):
                v.name = v.name or k
                stylesheet.append(v)


if __name__ == "__main__":
    with styles():
        Body = style(backgroundColor="${block.bg}").derive(
            "&:hover",
            backgroundColor="",
        )
    print("Body", Body.name)
# EOF
