from typing import Generic, TypeVar, Iterator, Any, NamedTuple

T = TypeVar("T")
V = TypeVar("V")


class Node(NamedTuple):
    id: Any
    value: Any
    children: list["Node"] | None = None


class TreeMatrix(Generic[T, V]):
    """Stores a tree in matricial format."""

    def __init__(self):
        self.children: dict[T, list[T]] = {}
        self.parents: dict[T, T] = {}
        self.nodes: dict[T, V] = {}

    def register(self, nid: T, node: V, parent: T | None = None):
        if nid in self.nodes:
            raise RuntimeError(f"Node already registered: {nid}")
        self.nodes[nid] = node
        if parent is not None:
            self.parents[nid] = parent
            self.children.setdefault(parent, []).append(nid)

        return self

    def roots(self) -> Iterator[T]:
        return (_ for _ in self.nodes if self.parents.get(_) is None)

    def walk(self, root: T) -> Iterator[T]:
        yield root
        for _ in self.children.get(root, ()):
            yield from self.walk(_)

    def asNode(self, node: T) -> Node:
        return Node(
            id=node,
            value=self.nodes[node],
            children=(
                [self.asNode(_) for _ in self.children.get(node)]
                if node in self.children
                else None
            ),
        )


# EOF
