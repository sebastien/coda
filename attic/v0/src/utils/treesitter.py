from tree_sitter import Language, Node, Tree, Parser
from pathlib import Path
from typing import Optional, Generator, Any
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


def getLanguages() -> dict[str, Language]:
    """Returns a map of available TreeSitter languages"""
    res: dict[str, Language] = {}
    for l in ["python", "javascript"]:
        match l:
            case "python":
                import tree_sitter_python as lang
            case "javascript":
                import tree_sitter_javascript as lang
            case _:
                raise ValueError(f"Unsupported language: {l}")
        res[l] = Language(lang.language())
    return res


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

    def on_start(self, tree, source, meta):
        """Called on parsing start"""
        pass

    def on_end(self, tree, source, meta):
        """Called on parsing end"""
        pass

    def process(self, tree: Tree, source: bytes, meta: Any | None = None):
        """Processes the given Treesitter Tree, parsed off the given
        `source`."""

        cursor = tree.walk()
        self.source = source
        depth = 0
        breadth = 0
        visited = set()
        on_exit = {}
        # NOTE: Not sure if we should call init there
        self.on_start(tree, source, meta)
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
                # FIXME: I'm not sure why this is the exit condition?
                if node_key(cursor.node) in visited:
                    while self.depth > 0:
                        self.pop()
                    return self.on_end(tree, source, meta)


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
        # TODO: We're not handling the assignment properly, ie.
        # class A:
        #   STATIC = 1
        #   SOMEVAR[1] = 10
        #   A,B = (10, 20)
        name_node = node.child_by_field_name("left")
        name = self.text(name_node) if name_node else None

        def on_exit(_, self=self):
            pass

        return on_exit

    def on_definition(
        self, node: Node, value: str, depth: int, breadth: int, type: str = "block"
    ):
        name_node = node.child_by_field_name("name")
        name = self.text(name_node) if name_node else None
        self.mode = "def"
        self.push()

        return self.pop

    def on_attribute(self, node: Node, value: str, depth: int, breadth: int):
        pass

    def on_type(self, node: Node, value: str, depth: int, breadth: int):
        pass

    # --
    # ### References
    def on_identifier(self, node: Node, value: str, depth: int, breadth: int):
        pass
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

        self.push()

        def on_exit(_):
            self.mode = mode
            self.pop()

        return on_exit

    def on_argument_list(self, node: Node, value: str, depth: int, breadth: int):
        self.push()
        return self.pop

    def on_string(self, node: Node, value: str, depth: int, breadth: int):
        self.push()
        return self.pop

    def on_binary_operator(self, node: Node, value: str, depth: int, breadth: int):
        mode = self.mode
        self.mode = "ref"

        def on_exit(_):
            self.mode = mode

        return on_exit

    def on_call(self, node: str, value: str, depth: int, breadth: int):
        self.push()
        return self.pop

    def on_paren_open(self, node: str, value: str, depth: int, breadth: int):
        self.mode = "ref"
        self.push()
        # NOTE: No pop required yet

    def on_paren_close(self, node: str, value: str, depth: int, breadth: int):
        self.pop()

    def on_dot(self, node: str, value: str, depth: int, breadth: int):
        # NOTE: This one is weird, as it does not contain a child
        pass

    def on_comma(self, node: str, value: str, depth: int, breadth: int):
        pass

    def on_equal(self, node: str, value: str, depth: int, breadth: int):
        self.mode = "ref"

    def on_node(self, node: str, value: str, depth: int, breadth: int):
        pass


# --
# ## Main

if __name__ == "__main__":
    languages = getLanguages()
    parser = Parser()
    parser.language = languages["python"]
    open_path = Path(__file__)
    open_path = "research/treesitter-extractor.py"
    with open(open_path, "rb") as f:
        text = f.read()
        tree = parser.parse(text)

    StructureProcessor().process(tree, text)
# EOF
