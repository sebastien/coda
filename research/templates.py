from dataclasses import dataclass
from typing import Optional, Iterable, Generic, TypeVar, Callable, Union, Any

T = TypeVar("T")


TLiteral = Optional[bool | int | float | str]
TComposite = list[TLiteral] | dict[str, TLiteral]
TPrimitive = TLiteral | TComposite
TTemplate = Union[
    TLiteral, "Slot", list[TLiteral | "Slot"], dict[str, TLiteral | "Slot"]
]
TAttributes = dict[str, TLiteral]


class Slot:
    IDS: int = 0

    @staticmethod
    def Apply(value: TTemplate, context: dict["Slot", TPrimitive]) -> TPrimitive:
        if isinstance(value, list):
            return [Slot.Apply(_, context) for _ in value]
        elif isinstance(value, dict):
            return {k: Slot.Apply(_, context) for k, _ in value.items()}
        elif isinstance(value, Slot):
            return context.get(value)
        else:
            return value

    def __init__(self, name: Optional[str] = None):
        self.id = Slot.IDS
        self.name = name
        self.effector: Optional[Effector] = None
        Slot.IDS += 1

    def __repr__(self):
        attrs = [f"id={self.id}"]
        if self.name:
            attrs.append(f'name="{self.name}"')
        return f"<slot {' '.join(attrs)} />"


class Effector:
    def apply(self, context: dict[Slot, TComposite]) -> Iterable["VNode"]:
        pass


class VNode:
    """A Virtual DOM Node with a simple API"""

    @classmethod
    def Factory(cls, name: str) -> Callable[[Any], "VNode"]:
        """Returns a factory function that can be used in a HyperScript
        style."""

        def factory(
            attr: Optional[TAttributes | VNode] = None,
            *children: VNode | Slot | TLiteral,
        ):
            return (
                cls(name, children=children)
                if attr is None
                else cls(name, attributes=attr, children=children)
                if isinstance(attr, dict)
                else cls(name, children=[attr] + [VNode.Ensure(_) for _ in children])
            )

        return factory

    @staticmethod
    def Ensure(value: Slot | TLiteral | "VNode") -> "VNode":
        """Ensures that the given value is wrapped in a VNode."""
        return value if isinstance(value, VNode) else VNode("#text", {"value": value})

    def __init__(
        self,
        name: str,
        attributes: Optional[dict[str, Slot | TLiteral]] = None,
        children: Optional[Iterable[Slot | TLiteral | "VNode"]] = None,
    ):
        self.name = name
        self.attributes: dict[str, Slot | TLiteral] = (
            {k: v for k, v in attributes.items()} if attributes else {}
        )
        self.children: list[VNode] = (
            [VNode.Ensure(_) for _ in children] if children else []
        )

    def apply(self, context: dict[Slot, TPrimitive]) -> "VNode":
        """Returns a new VNode with the application of the the given context
        to the slots"""
        return VNode(
            name=self.name,
            attributes=Slot.Apply(self.attributes, context),
            children=[_.apply(context) for _ in self.children],
        )

    def __repr__(self):
        if self.name == "#text":
            return f"{self.attributes['value']}"
        else:
            sq = "'"
            dq = '"'
            a = " ".join(
                f"{k}={str(v).replace(dq,sq)}" for k, v in self.attributes.items()
            )
            attrs = f" {a}" if a else ""
            if not self.children:
                return f"<{self.name}{attrs}/>"
            else:

                return f"<{self.name}{attrs}>{''.join(repr(_) for _ in self.children)}</{self.name}>"


class Proxy(Generic[T]):
    def __init__(
        self, creator: Callable[[str], T], state: Optional[dict[str, T]] = None
    ):
        self._creator = creator
        self._state = {} if state is None else state

    def __getattr__(self, name: str) -> T:
        if name.startswith("_"):
            return object.__getattr__(self, name)
        elif name in (state := self._state):
            return state[name]
        else:
            state[name] = (res := self._creator(name))
            return res


def slot(name: Optional[str] = None) -> Slot:
    return Slot(name)


if __name__ == "__main__":
    print("=== TEST templates: Rendering")
    h = Proxy(VNode.Factory)
    print(h.div("Hello, ", name := slot()).apply({name: "World"}))
    print("--- EOK")


# EOF
