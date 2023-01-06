from typing import NamedTuple, Optional, ClassVar
import re

# --
# # Design tokens

RE_TOKEN = re.compile(
    r"(\\.(?P<key>[A-Za-z_]+)(?P<factor>\\d+)|(?P<value>\\d+(\\.\\d+)?)(?P<unit>[A-Za-z]+)|(?P<name>[A-Za-z_]+))"
)


class TokenChunk(NamedTuple):
    type: str
    name: str
    factor: Optional[int] = None


def token(text: str) -> Token:
    n: int = len(text)
    o: int = 0
    r: list[TokenChunk] = []
    while match := RE_TOKEN.match(text, o):
        if key := match.group("key"):
            r.append(TokenChunk("factor", key, int(match.group("factor"))))
        pass


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
            return Color(
                Color.Degamma(
                    SRGBA(
                        int(r, 16) / 255.0 if r else 0.0,
                        int(g, 16) / 255.0 if g else 0.0,
                        int(b, 16) / 255.0 if b else 0.0,
                        int(a, 16) / 255.0 if a else 1.0,
                    )
                )
            )
        else:
            raise ValueError(f"Could not parse RGBA value: {value}")

    @staticmethod
    def Gamma(rgba: LinearRGBA) -> SRGBA:
        return SRGBA(
            *(
                _ * 12.92 if _ <= 0.00304 else 1.055 * pow(_, 1.0 / 2.4) - 0.055
                for _ in rgba
            )
        )

    @staticmethod
    def Degamma(srgba: SRGBA) -> LinearRGBA:
        return LinearRGBA(
            *(
                _ / 12.92 if _ <= 0.03928 else pow((_ + 0.055) / 1.055, 2.4)
                for _ in srgba
            )
        )

    @staticmethod
    def Luminance(rgba: LinearRGBA) -> float:
        r, g, b, _ = rgba
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    @staticmethod
    def DarkLight(
        a: None | "Color" = None, b: None | "Color" = None
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
        r, g, b, a = self.value
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
        dark: None | "Color" = None,
        light: None | "Color" = None,
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
        self, steps: int = 10, dark: None | "Color" = None, light: None | "Color" = None
    ) -> list["Color"]:
        dk, lt = Color.DarkLight(dark, light)
        return [self.tint(i / float(steps), dk, lt) for i in range(steps + 1)]

    def __str__(self) -> str:
        return f'#{"".join((f"{_*255.0:02x}" for _ in Color.Gamma(self.value)))}'


if __name__ == "__main__":
    tokens = dict(
        Blue="#198ebe",
        Background="#FFFFFF",
        focused=lambda _: _.color.grey(0.5).alpha(0.25),
    )

    print(token("Blue.focused"))

# --
# ## References
#
# - https://observablehq.com/@sebastien/tokens

# EOF
