from tree_sitter import Language, Node, Tree, Parser
from pathlib import Path
from typing import Optional
import os

# TODO: Given an instruction to swallow children, for instance

#       -   a: int
#           =   a
#           @   a
#           -   <Node kind=":", start_point=(8, 5), end_point=(8, 6)>
#           TYP int
#           @   int

# Should be
#       -   a: int
#           =   a
#           -   <Node kind=":", start_point=(8, 5), end_point=(8, 6)>
#           TYP int


# --
# Ensures that tree-sitter is working properly and that the grammars
# are also working properly.

# FROM: https://github.com/tree-sitter/py-tree-sitter


BASE = Path(__file__).parent
REPOS = Path(__file__).parent.parent.parent.parent / ".deps/src"


def getLanguages(
    path: Optional[Path] = None, repos: Optional[Path] = None
) -> dict[str, Language]:
    """Returns a map of available TreeSitter languages"""
    lib_path = str(path or BASE / "treesitter-languages.so")
    repo_base = repos or REPOS
    langs = [
        _.split("-", 3)[2]
        for _ in os.listdir(repo_base)
        if _.startswith("tree-sitter-")
    ]
    Language.build_library(
        # Store the library in the `build` directory
        str(lib_path),
        [str(repo_base / f"tree-sitter-{lang}") for lang in langs],
    )
    return {lang: Language(lib_path, lang) for lang in langs}


# --
# ## Tree Processor


def node_key(node: Node) -> str:
    """Returns a unique identifier for a given node. Unicity is within
    a tree."""
    return f"{node.type}:{node.start_byte}:{node.end_byte}"


class Processor:
    """Base class to write TreeSitter processors."""

    ALIASES = {
        "+": "plus",
        "-": "minus",
        "*": "times",
        "/": "slash",
        "**": "timetime",
        "^": "chevron",
        "(": "paren_open",
        ")": "paren_close",
        ",": "comma",
        ".": "dot",
        "=": "equal",
    }

    def __init__(self):
        self.init()
        self.source: bytes = b""

    def init(self):
        pass

    def text(self, node: Node) -> str:
        return str(self.source[node.start_byte : node.end_byte], "utf8")

    def on_node(self, node: Node, value: str, depth: int, breadth: int):
        """Called on node"""
        print(f"node:{node.type} {depth}+{breadth}")

    def on_start(self):
        """Called on parsing start"""
        pass

    def on_end(self):
        """Called on parsing end"""
        pass

    def process(self, tree: Tree, source: bytes):
        """Processes the given Treesitter Tree, parsed off the given
        `source`."""

        cursor = tree.walk()
        self.source = source
        depth = 0
        breadth = 0
        visited = set()
        on_exit = {}
        # NOTE: Not sure if we should call init there
        self.on_start()
        # This implements a depth-first traversal of the tree
        while True:
            node = cursor.node
            key = node_key(node)
            method_name = f"on_{self.ALIASES.get(node.type, node.type)}"
            processor = (
                getattr(self, method_name)
                if hasattr(self, method_name)
                else self.on_node
            )
            exit_functor = processor(node, self.text(node), depth, breadth)
            # We use functors as exit functions
            if exit_functor:
                if node.child_count > 0:
                    on_exit[key] = exit_functor
                else:
                    exit_functor(node)
            visited.add(node_key(node))
            if cursor.goto_first_child():
                breadth = 0
                depth += 1
            elif cursor.goto_next_sibling():
                breadth += 1
            else:
                # When we go up, we need to be careful.
                previous_key = node_key(cursor.node)
                while depth > 0:
                    previous_node = cursor.node
                    breadth = 0
                    cursor.goto_parent()
                    current_key = node_key(cursor.node)
                    if current_key == previous_key:
                        break
                    else:
                        # This is the on exit on the way up
                        if previous_key in on_exit:
                            on_exit[previous_key](previous_node)
                            del on_exit[previous_key]
                        previous_key = current_key
                    depth -= 1
                    # We skip the visited nodes
                    while (previous_key := node_key(cursor.node)) in visited:
                        # This is the on exit on the way to the next sibling
                        if previous_key in on_exit:
                            on_exit[previous_key](cursor.node)
                            del on_exit[previous_key]
                        if cursor.goto_next_sibling():
                            breadth += 1
                        else:
                            break
                    if node_key(cursor.node) not in visited:
                        break
                if node_key(cursor.node) in visited:
                    return self.on_end()


# --
# ## Program Structure Processing


class StructureProcessor(Processor):
    def init(self):
        self.mode = None
        self.depth: int = 0

    def push(self):
        self.depth += 1

    def pop(self, node: Optional[Node] = None):
        self.depth -= 1

    # --
    # ### Structure

    def on_class(self, node: Node, value: str, depth: int, breadth: int):
        self.push()
        self.mode = "decl"
        return self.pop

    def on_block(self, node: Node, value: str, depth: int, breadth: int):
        self.push()
        self.mode = "def"
        return self.pop

    # --
    # ### Definitions

    def on_function_definition(self, node: Node, value: str, depth: int, breadth: int):
        return self.on_definition(node, value, depth, breadth, "function")

    def on_class_definition(self, node: Node, value: str, depth: int, breadth: int):
        return self.on_definition(node, value, depth, breadth, "class")

    def on_assignment(self, node: Node, value: str, depth: int, breadth: int):
        # TODO: We're not handling the asssignment properly, ie.
        # class A:
        #   STATIC = 1
        #   SOMEVAR[1] = 10
        #   A,B = (10, 20)
        name_node = node.child_by_field_name("left")
        name = self.text(name_node) if name_node else None
        print(f"{'    ' * self.depth}=   {name}")
        # self.scope = self.scope.derive(
        #     type=type, range=(node.start_byte, node.end_byte), name=name
        # )

        def on_exit(_, self=self):
            pass
            # self.scope = self.scope.parent

        return on_exit

    def on_definition(
        self, node: Node, value: str, depth: int, breadth: int, type: str = "block"
    ):
        name_node = node.child_by_field_name("name")
        name = self.text(name_node) if name_node else None
        print(f"{'    ' * self.depth}DEF {name}")
        # self.scope = self.scope.derive(
        #     type=type, range=(node.start_byte, node.end_byte), name=name
        # )
        self.mode = "def"
        self.depth += 1

        def on_exit(_, self=self):
            # self.scope = self.scope.parent
            self.depth -= 1
            pass

        return on_exit

    def on_attribute(self, node: Node, value: str, depth: int, breadth: int):
        # FIXME: Not sure this is what I think it is, ie:
        #         ATT StructureProcessor().process
        pass
        # print(f"{'    ' * self.depth}ATT {self.text(node)}")
        # self.push()
        # return self.pop

    def on_type(self, node: Node, value: str, depth: int, breadth: int):
        print(f"{'    ' * self.depth}TYP {self.text(node)}")

    # --
    # ### References
    def on_identifier(self, node: Node, value: str, depth: int, breadth: int):
        print(
            f"{'    ' * self.depth}{'=  ' if self.mode == 'def' else '@  '} {self.text(node)}"
        )
        # if value not in self.scope.slots:
        #     if self.mode == "ref":
        #         self.scope.refs[value] = self.mode
        #     else:
        #         self.scope.slots[value] = self.mode

    def on_with_statement(self, node: Node, value: str, depth: int, breadth: int):
        return self.on_statement(node, value, depth, breadth)

    def on_return_statement(self, node: Node, value: str, depth: int, breadth: int):
        return self.on_statement(node, value, depth, breadth)

    # NOTE: Assignments are contained in expressions, so maybe not ideal
    # def on_expression_statement(self, node: Node, value: str, depth: int, breadth: int):
    #     print("ON:EXPR", node.sexp())
    #     if self.scope.type != "module":
    #         return self.on_statement(node, value, depth, breadth)
    #     else:
    #         self.scope = self.scope.derive(
    #             type="expression", range=(node.start_byte, node.end_byte))
    #         self.mode = "def"
    #         self.on_statement(node, value, depth, breadth)

    #         def on_exit(_, self=self):
    #             self.scope = self.scope.parent
    #         return on_exit

    def on_expression_statement(self, node: Node, value: str, depth: int, breadth: int):
        return self.on_statement(node, value, depth, breadth)

    def on_statement(self, node: Node, value: str, depth: int, breadth: int):
        mode = self.mode
        self.mode = "ref"

        print(f"{'    ' * self.depth}-   {self.text(node)}")
        self.depth += 1

        def on_exit(_):
            self.mode = mode
            self.depth -= 1

        return on_exit

    def on_argument_list(self, node: Node, value: str, depth: int, breadth: int):
        self.push()
        return lambda _: self.pop()

    def on_string(self, node: Node, value: str, depth: int, breadth: int):
        self.push()
        return lambda _: self.pop()

    def on_binary_operator(self, node: Node, value: str, depth: int, breadth: int):
        mode = self.mode
        self.mode = "ref"

        def on_exit(_):
            self.mode = mode

        return on_exit

    def on_call(self, node: str, value: str, depth: int, breadth: int):
        print(f"{'    ' * self.depth}:invocation")
        self.push()
        return self.pop

    def on_paren_open(self, node: str, value: str, depth: int, breadth: int):
        print(f"{'    ' * self.depth}:list")
        self.mode = "ref"
        self.push()

    def on_paren_close(self, node: str, value: str, depth: int, breadth: int):
        self.pop()

    def on_dot(self, node: str, value: str, depth: int, breadth: int):
        # NOTE: This one is weird, as it does not contain a child
        print(f"{'    ' * self.depth}:resolve")

    def on_comma(self, node: str, value: str, depth: int, breadth: int):
        pass

    def on_equal(self, node: str, value: str, depth: int, breadth: int):
        self.mode = "ref"

    def on_node(self, node: str, value: str, depth: int, breadth: int):
        print(f"{'    ' * self.depth}-   {node}")
        pass


# --
# ## Main

languages = getLanguages()
parser = Parser()
parser.set_language(languages["python"])
open_path = Path(__file__)
open_path = "test.py"
with open(open_path, "rb") as f:
    text = f.read()
    tree = parser.parse(text)

StructureProcessor().process(tree, text)
# EOF
