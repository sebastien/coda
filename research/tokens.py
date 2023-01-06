from typing import NamedTuple, Optional, ClassVar, Iterable, Callable, TypeAlias, Union
from dataclasses import dataclass
import re
import inspect

# -- # Design tokens


TValue: TypeAlias = Optional[Union[str, int, float, bool, "Color"]]
TContextValue: TypeAlias = Union[TValue, Callable[["TokenContext"], TValue]]


class TokenChunk(NamedTuple):
    type: str
    name: str
    factor: Optional[int] = None


@dataclass
class TokenContext:
    value: TValue
    color: "Color"
    context: dict[str, TValue]

    def __call__(self, name: str) -> TValue:
        value = self.context[name]
        return value


class Token:
    CHUNK: ClassVar[
        str
    ] = r"(?P<key>[A-Za-z_]+)(?P<factor>\\d+)|(?P<value>\\d+(\\.\\d+)?)(?P<unit>[A-Za-z]+)|(?P<name>[A-Za-z_]+)"
    CHUNK_ANON: ClassVar[str] = re.sub("\\?P\\<\\w+\\>", "", CHUNK)
    RE_CHUNK: ClassVar[re.Pattern[str]] = re.compile(CHUNK)
    RE_EXPR: ClassVar[re.Pattern[str]] = re.compile(r"\${(?P<content>[^}]+)}")

    @staticmethod
    def Expand(text: str, context: dict[str, TContextValue]) -> str:
        o: int = 0
        r: list[str] = []
        while match := Token.RE_EXPR.search(text, o):
            r.append(text[o : match.start()])
            if token := Token.Parse(match["content"]):
                r.append(str(token.eval(context).value))
            else:
                r.append(match.group())
            o = match.end()
        r.append(text[o:])
        return "".join(r)

    @staticmethod
    def Parse(text: str, strict: bool = True) -> Optional["Token"]:
        n: int = len(text)
        o: int = 0
        r: list[TokenChunk] = []
        while match := Token.RE_CHUNK.match(text, o):
            if key := match.group("key"):
                r.append(TokenChunk("factor", key, int(match["factor"])))
            elif name := match.group("name"):
                r.append(TokenChunk("symbol", name))
            elif value := match.group("value"):
                r.append(TokenChunk("metrics", match["unit"], int(match["factor"])))
            else:
                raise NotImplementedError
            o = match.end()
            if o >= n:
                break
            elif text[o] != ".":
                if strict:
                    raise ValueError(
                        f"Token should have a dot at {o}, got '{text[o]}' in: '{text}'"
                    )
                else:
                    return None
            else:
                o += 1
        if strict and o < n:
            raise ValueError(f"Could not parse token, stopped at {o} in: '{text}'")
        else:
            return Token(r) if o >= n else None

    @staticmethod
    def Resolve(
        name: str,
        factor: Optional[float],
        parent: TokenContext,
    ) -> TokenContext:
        # FIXME: Not sure why we need context here, actually
        value: Optional[TValue] = parent.context.get(name)
        if value is None:
            raise ValueError(f"Undefined token '{name}'")
        elif isinstance(value, str):
            return TokenContext(value, parent.color, parent.context)
        elif isinstance(value, Color):
            return TokenContext(value, value, parent.context)
        elif inspect.isfunction(value):
            k = len(inspect.signature(value).parameters)
            w = value(parent, factor) if k >= 2 else value(parent)
            return TokenContext(
                w, w if isinstance(w, Color) else parent.color, parent.context
            )
        else:
            raise ValueError(f"Unsupported value type '{type(value)}': {value}")

    @staticmethod
    def Eval(chunks: Iterable[TokenChunk], context: dict[str, TValue]):

        res = TokenContext(None, Color(LinearRGBA(0.0, 0.0, 0.0)), context)
        for v in chunks:
            r = Token.Resolve(v.name, v.factor, res)
            res = TokenContext(
                r.value,
                (r.value if isinstance(r.value, Color) else res.color),
                r.context,
            )
        return res

    def __init__(self, chunks: Iterable[TokenChunk]):
        self.chunks = [_ for _ in chunks]

    def eval(self, context: dict[str, TContextValue]):
        return Token.Eval(self.chunks, context)


def token(text: str) -> Token:
    return Token.Parse(text)


def expand(text, context: dict[str, TContextValue]) -> str:
    return Token.Expand(text, context)


# --
# ## Math Utilities


class Math:
    @staticmethod
    def Lerp(a: float, b: float, k: float) -> float:
        return a + (b - a) * k

    @staticmethod
    def Prel(v, a: float, b: float) -> float:
        return (v - a) / (b - a)

    @staticmethod
    def Clamp(v: float, a: float = 0.0, b: float = 1.0) -> float:
        a, b = min(a, b), max(a, b)
        return min(max(a, b), max(v, min(a, b)))

    @staticmethod
    def Minmax(*values: float) -> tuple[float, float]:
        mn: float = 0.0
        mx: float = 0.0
        for i, v in enumerate(values):
            mn = v if i == 0 or v < mn else mn
            mx = v if i == 0 or v > mx else mx
        return mn, mx

    @staticmethod
    def Steps(count: int) -> list[float]:
        return [float(_) / float(count) for _ in range(count)] + [1.0]


# --
# ## Color Utilities


class LinearRGBA(NamedTuple):
    """An RGBA quadruple in linear space"""

    r: float
    g: float
    b: float
    a: float = 1.0


class SRGBA(NamedTuple):
    r: float
    g: float
    b: float
    a: float = 1.0


class Color:
    RE_RGBA: ClassVar[re.Pattern[str]] = re.compile(
        r"#?(?P<r>[A-Fa-f0-9][A-Fa-f0-9])(?P<g>[A-Fa-f0-9][A-Fa-f0-9])(?P<b>[A-Fa-f0-9][A-Fa-f0-9])(?P<a>[A-Fa-f0-9][A-Fa-f0-9])?"
    )

    @classmethod
    def Parse(cls, value: str) -> "Color":
        if match := Color.RE_RGBA.match(value):
            r, g, b, a = (match.group(_) for _ in ("r", "g", "b", "a"))
            c = SRGBA(
                int(r, 16) / 255.0 if r else 0.0,
                int(g, 16) / 255.0 if g else 0.0,
                int(b, 16) / 255.0 if b else 0.0,
                int(a, 16) / 255.0 if a else 1.0,
            )
            return Color(Color.Degamma(c))
        else:
            raise ValueError(f"Could not parse RGBA value: {value}")

    @staticmethod
    def Gamma(rgba: LinearRGBA) -> SRGBA:
        return SRGBA(
            *(
                _
                if i >= 3
                else (_ * 12.92 if _ <= 0.00304 else 1.055 * pow(_, 1.0 / 2.4) - 0.055)
                for i, _ in enumerate(rgba)
            )
        )

    @staticmethod
    def Degamma(srgba: SRGBA) -> LinearRGBA:
        return LinearRGBA(
            *(
                _
                if i >= 3
                else (_ / 12.92 if _ <= 0.03928 else pow((_ + 0.055) / 1.055, 2.4))
                for i, _ in enumerate(srgba)
            )
        )

    @staticmethod
    def Luminance(rgba: LinearRGBA) -> float:
        r, g, b, _ = rgba
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    @staticmethod
    def DarkLight(
        a: Optional["Color"] = None, b: Optional["Color"] = None
    ) -> tuple["Color", "Color"]:
        ca = a or Color(LinearRGBA(0.0, 0.0, 0.0))
        cb = b or Color(LinearRGBA(1.0, 1.0, 1.0))
        return (ca, cb) if ca.luminance < cb.luminance else (cb, ca)

    def __init__(self, value: LinearRGBA):
        self.value: LinearRGBA = value

    @property
    def luminance(self) -> float:
        return Color.Luminance(self.value)

    def alpha(self, k: float = 1.0) -> "Color":
        r, g, b, _ = self.value
        return Color(LinearRGBA(r, g, b, min(1.0, max(0.0, k))))

    def grey(self, k: float = 1.0) -> "Color":
        l = self.luminance
        g = Color(LinearRGBA(l, l, l, 1.0))
        return g if k >= 1 else self.blend(g, k)

    def blend(self, color: "Color", k: float = 0.5) -> "Color":
        return Color(
            LinearRGBA(
                *(
                    Math.Clamp(Math.Lerp(v, color.value[i], k), 0, 1)
                    for i, v in enumerate(self.value)
                )
            )
        )

    def tint(
        self,
        luminance: float = 0.5,
        dark: Optional["Color"] = None,
        light: Optional["Color"] = None,
    ) -> "Color":
        dk, lt = Color.DarkLight(dark, light)
        l = Math.Clamp(self.luminance)
        v = Math.Clamp(luminance)
        return (
            self.blend(lt, Math.Prel(v, l, lt.luminance))
            if l < v
            else self.blend(dk, Math.Prel(v, l, dk.luminance))
        )

    def scale(
        self,
        steps: int = 10,
        dark: Optional["Color"] = None,
        light: Optional["Color"] = None,
    ) -> list["Color"]:
        dk, lt = Color.DarkLight(dark, light)
        return [self.tint(i / float(steps), dk, lt) for i in range(steps + 1)]

    def __repr__(self) -> str:
        return f'#{"".join((f"{round(_*255):02X}" for _ in Color.Gamma(self.value)))}'


def color(color: Color | str) -> Color:
    return color if isinstance(color, Color) else Color.Parse(color)


if __name__ == "__main__":
    print("=== TEST: Design tokens subsitution")
    tokens: dict[str, TContextValue] = dict(
        Blue=color("#198ebe"),
        Background=color("#FFFFFF"),
        focused=lambda _: _.color.tint(_.color.luminance + 0.15),
    )

    print(expand("color: ${Blue.focused}", tokens))

# --
# ## References
#
# - https://observablehq.com/@sebastien/tokens

# EOF
