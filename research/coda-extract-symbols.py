from typing import NamedTuple
from coda.collect.files import Files
from coda.utils.treematrix import TreeMatrix
from coda.utils.treesitter import Node, StructureProcessor, getLanguages, Parser
from coda.utils.json import asJSON
import os


class Module(NamedTuple):
    name: str
    path: str


class Fragment(NamedTuple):
    source: str
    start: int
    end: int


class Symbol(NamedTuple):
    id: str
    name: str
    type: str
    fragment: Fragment
    parent: str | None = None


languages = getLanguages()
parser = Parser()
parser.language = languages["python"]

cat = Files.Catalogue(
    Files.Filter(Files.Walk("src"), includes=["*.py", "*.sh", "*.js"])
)


class Registered(NamedTuple):
    type: str
    name: str
    node: Node


class Processor(StructureProcessor):

    def __init__(self):
        super().__init__()
        self.stack = []
        self.module = None
        self.tree: TreeMatrix[str, Symbol] = TreeMatrix()

    def register(self, value: Registered, depth: int):
        while len(self.stack) < depth:
            self.stack.append([])
        while len(self.stack) > depth:
            self.stack.pop()
        parent = None
        ancestors = [self.module.name]
        for i in range(0, depth - 2):
            if self.stack[i]:
                ancestors.append(self.stack[i][-1][1])
        parent = ".".join(ancestors)
        symbol = Symbol(
            id=(nid := f"{parent}.{value.name}"),
            parent=parent,
            name=value.name,
            type=value.type,
            fragment=Fragment(
                self.module.path, value.node.start_byte, value.node.end_byte
            ),
        )
        self.tree.register(nid, symbol, parent)
        self.stack[-1].append(value)

    def on_start(self, tree, source, meta):
        """Called on parsing start"""
        res = super().on_start(tree, source, meta)
        self.tree.register(
            meta.name,
            Symbol(
                meta.name,
                parent=None,
                name=meta,
                type="module",
                fragment=Fragment(meta.path, 0, len(source)),
            ),
        )
        self.module = meta
        return res

    def on_definition(
        self, node: Node, value: str, depth: int, breadth: int, type: str = "block"
    ):
        on_exit = super().on_definition(node, value, depth, breadth, type)
        name_node = node.child_by_field_name("name")
        name = self.text(name_node) if name_node else None
        self.register(Registered(type, name, node), depth)
        return on_exit

    def on_assignment(self, node: Node, value: str, depth: int, breadth: int):
        on_exit = super().on_assignment(node, value, depth, breadth)
        # TODO: We're not handling the assignment properly, ie.
        # class A:
        #   STATIC = 1
        #   SOMEVAR[1] = 10
        #   A,B = (10, 20)
        name_node = node.child_by_field_name("left")
        name = self.text(name_node) if name_node else None
        # We skip that for now
        # self.register(("var", name), depth)
        return on_exit


processor = Processor()
for node in cat.nodes.values():
    if not node.file:
        continue
    print("\n === FFFFILE", node.id)
    path = f"src/{node.id}"
    name = (
        node.id.replace("src/py", "")
        .replace("/", ".")
        .replace("py.", "")
        .replace(".py", "")
    )
    with open(path, "rb") as f:
        source = f.read()
        tree = parser.parse(source)
        processor.process(tree, source, Module(name=name, path=path))

with open("research/data/symbols.json", "wt") as f:
    f.write(asJSON([processor.tree.asNode(_) for _ in processor.tree.roots()]))


# EOF
