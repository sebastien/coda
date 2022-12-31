from dataclasses import dataclass
from typing import Optional, Iterable, Generic, TypeVar, Callable, Union, Any

# --
# # Templates
#
# This notebook defines primitives to create tree templates that can be
# rendered to HTML.

T = TypeVar("T")

# --
# ## Types

TLiteral = Optional[bool | int | float | str]
TComposite = list[TLiteral] | dict[str, TLiteral]
TPrimitive = TLiteral | TComposite
TTemplate = Union[
    TLiteral, "Slot", list[TLiteral | "Slot"], dict[str, TLiteral | "Slot"]
]
TAttributes = dict[str, TLiteral]
Treeish = Union[None, TPrimitive, "VNode", list[Union[TPrimitive, "VNode"]]]

# --
# ## Slots


class Slot:
    IDS: int = 0

    # WIP
    _Accessor: Optional["Proxy[Slot]"] = None

    # WIP -- The accessor is meant as a way to manage the implicit `_`
    @classmethod
    def Accessor(cls) -> "Proxy[Slot]":
        if not cls._Accessor:
            cls._Accessor = Proxy(lambda _: Slot())
        return cls._Accessor

    @staticmethod
    def Apply(value: TTemplate, context: dict["Slot", TPrimitive]) -> Treeish:
        if isinstance(value, list):
            return [Slot.Apply(_, context) for _ in value]
        elif isinstance(value, dict):
            return {k: Slot.Apply(_, context) for k, _ in value.items()}
        elif isinstance(value, Slot):
            # We let the specific type of slot apply itself. For instance,
            # Effect slots will do their thing here.
            return value.apply(context)
        else:
            return value

    def __init__(self):
        self.id = Slot.IDS
        Slot.IDS += 1

    def apply(self, context: dict["Slot", TComposite]) -> Treeish:
        return context.get(self)

    def __repr__(self):
        return f"<slot id={self.id} />"


class Input(Slot):
    def map(self, *nodes: "VNode") -> "Effect":
        return Effect(self, MappingEffector(nodes))


class Argument(Input):
    def __init__(self, name: str):
        super().__init__()
        self.name = name


# --
# ## Effects


class Effect(Slot):
    def __init__(self, source: Slot, effector: "Effector"):
        super().__init__()
        self.source: Slot = source
        self.effector: Effector = effector

    def apply(self, context: dict["Slot", TComposite]) -> Treeish:
        return self.effector.apply(self.source.apply(context), context)

    def __repr__(self):
        return f"<effect:{self.effector.__class__.__name__.replace('Effector','').lower()} id={self.id} />"


class Effector:
    def apply(self, value: TPrimitive, context: dict[Slot, TComposite]) -> Treeish:
        pass


class MappingEffector(Effector):
    def __init__(self, nodes: Iterable["VNode"]):
        super().__init__()
        self.nodes = [_ for _ in nodes]

    def apply(
        self,
        value: TPrimitive,
        context: dict[Slot, TPrimitive],
    ) -> Treeish:
        if isinstance(value, list):
            return [node.apply(context) for node in self.nodes]
        elif isinstance(value, dict):
            pass
        print("VALUE", value)
        return "OK"


# --
# ## Virtual Nodes


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

    def __str__(self):
        """The string representation is straight up HTML"""
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

                return f"<{self.name}{attrs}>{''.join(str(_) for _ in self.children)}</{self.name}>"


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


def slot() -> Input:
    return Input()


# This is the global "current" scope
_: Proxy[Argument] = Proxy(lambda _: Argument(_))

if __name__ == "__main__":
    print("=== TEST templates: Rendering")
    h = Proxy(VNode.Factory)
    print(h.div("Hello, ", name := slot()).apply({name: "World"}))
    items = slot()
    print(h.ul(items.map(h.li(_))).apply({items: ["One", "Two", "Three"]}))
    print("--- EOK")

# EOF
