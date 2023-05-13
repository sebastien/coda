from dataclasses import dataclass
import inspect
from typing import (
    Optional,
    Iterable,
    Generic,
    TypeVar,
    Callable,
    Union,
    ClassVar,
    Any,
    ContextManager,
)

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

    # List of reserved names
    RESERVED: ClassVar[list[str]] = ["map", "apply"]

    def __init__(self, key: str | int):
        super().__init__()
        self._key: str | int = key

    def __getattr__(self, name: str | int):
        if name in Argument.RESERVED or name.startswith("_"):
            return super().__getattr__(name)
        else:
            return Destructured(self, name)

    def __getitem__(self, name: str | int):
        return Destructured(self, name)


class Destructured(Argument):
    def __init__(self, parent: Argument, key: str | int):
        super().__init__(key)
        self._parent = parent

    def apply(self, context: dict["Slot", TComposite]) -> Treeish:
        res = self._parent.apply(context)
        if isinstance(res, dict):
            return res.get(self._key)
        elif isinstance(res, list) or isinstance(res, tuple):
            return res[self._key]
        else:
            return None


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
            res: list[VNode] = []
            for v in value:
                ctx = context | {CurrentSlot: v}
                for n in (node.apply(ctx) for node in self.nodes):
                    res.append(n)
            return res
        elif isinstance(value, dict):
            return self.apply([_ for _ in value.items()], context)
        elif value is not None:
            return self.apply([value], context)
        else:
            return None


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
        if isinstance(value, VNode):
            return value
        elif type(value) in (str, int, float, bool) or value is None:
            return VNode("#text", {"value": value})
        elif isinstance(value, Slot):
            return VNode("#slot", {"value": value})
        elif value is CurrentSelector:
            return VNode("#slot", {"value": CurrentSlot})
        else:
            raise ValueError(f"Unsupported value type '{type(value)}': {value}")

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

    @property
    def value(self) -> Optional[TPrimitive | Slot]:
        return self.attributes.get("value")

    def apply(self, context: dict[Slot, TPrimitive]) -> "VNode":
        """Returns a new VNode with the application of the the given context
        to the slots"""
        children: list[VNode] = []
        # NOTE: This seems a bit contrived, I supposed an iteartor may
        # be better?
        for child in self.children:
            if child.name == "#slot":
                applied = child.value.apply(context)
                if isinstance(applied, list):
                    for _ in applied:
                        children.append(VNode.Ensure(_))
                elif applied is not None:
                    children.append(VNode.Ensure(applied))
            else:
                children.append(child.apply(context))

        return VNode(
            name=self.name,
            attributes=Slot.Apply(self.attributes, context),
            children=children,
        )

    def __repr__(self):
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


class VNodeFactory(ContextManager):

    Stack: ClassVar[list[VNode]] = []

    def __init__(self, name: str):
        self.name: str = name

    def __enter__(
        self,
        attr: Optional[TAttributes | VNode] = None,
        *children: VNode | Slot | TLiteral,
    ):
        node = self(attr, *children)
        if VNodeFactory.Stack:
            VNodeFactory.Stack[-1].children.append(node)
        VNodeFactory.Stack.append(node)
        return node

    def __exit__(self, *context):
        node = VNodeFactory.Stack.pop()
        # for k, v in (inspect.currentframe().f_back.f_locals).items():
        #     pass

    def __call__(
        self,
        attr: Optional[TAttributes | VNode] = None,
        *children: VNode | Slot | TLiteral,
    ) -> VNode:
        return (
            VNode(self.name, children=children)
            if attr is None
            else VNode(self.name, attributes=attr, children=children)
            if isinstance(attr, dict)
            else VNode(self.name, children=[attr] + [VNode.Ensure(_) for _ in children])
        )


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


# This is the current slot
CurrentSlot: Argument = Argument("_")
_ = CurrentSlot

# This is the global "current" scope


@Proxy
def h(name: str) -> VNodeFactory:
    return VNodeFactory(name)


if __name__ == "__main__":
    print("=== TEST templates: Rendering")
    print(h.div("Hello, ", name := slot()).apply({name: "World"}))
    print("=== TEST templates: Rendering with context")
    with h.html as doc:
        with h.body as _:
            # TODO: Mixing both context and non-context does not work 100%
            _.children.append(h.h1("Hello, World!"))
    print(f"... doc={doc}")
    print("--- TEST effect: Mapping")
    items = slot()
    print(
        h.ul(items.map(h.li(h.span("My name is ", _)))).apply(
            {items: ["One", "Two", "Three"]}
        )
    )
    print("--- TEST effect: Mapping with destructuring")
    print(
        h.ul(items.map(h.li(h.span("My name is ", _.name)))).apply(
            {items: [{"name": "One"}, {"name": "Two"}]}
        )
    )
    print("--- EOK")

# EOF
