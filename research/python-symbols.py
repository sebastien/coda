import ast
from pathlib import Path
from typing import Iterator, NamedTuple, Optional
from html import escape


# -- prompt
# Can you write me a Python function "iterSymbols(source:Path,
# moduleName:str)->Iterator[Symbol]" that given a path to a Python file and its
# fully qualified module name, returns an iterator on Symbol objects like so:
#
#  Could you expand the above to support the following:
# - Imported modules
# - Imported symbols from modules
# - Function, static methods, class methods, constructor, methods
# - Function parameter, in which case their qualname should be prefixed by their parent function's qualname
# Thanks!


class Symbol(NamedTuple):
    name: str
    qualname: str
    type: str
    documentation: Optional[str]
    sourcePath: str
    range: "TextRange"


class TextRange(NamedTuple):
    startLine: int
    startColumn: int
    endLine: Optional[int]
    endColumn: Optional[int]


def rangeFromNode(node: ast.AST) -> TextRange:
    return TextRange(
        node.lineno - 1,
        node.col_offset,
        node.end_lineno - 1,
        node.end_col_offset,
    )


class SymbolVisitor(ast.NodeVisitor):
    def __init__(self, source: Path, moduleName: str, parentName: str = ""):
        self.source = source
        self.moduleName = moduleName
        self.parentName = parentName
        self.symbols = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.symbols.append(
                Symbol(
                    name=alias.name,
                    qualname=f"{self.moduleName}.{alias.name}",
                    type="module",
                    documentation=None,
                    sourcePath=str(self.source),
                    range=rangeFromNode(node),
                )
            )

    def visit_ClassDef(self, node: ast.ClassDef):
        qualname = (
            f"{self.moduleName}.{node.name}"
            if self.parentName == ""
            else f"{self.parentName}.{node.name}"
        )
        self.symbols.append(
            Symbol(
                name=node.name,
                qualname=qualname,
                type="class",
                documentation=ast.get_docstring(node),
                sourcePath=str(self.source),
                range=rangeFromNode(node),
            )
        )

        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in {"NamedTuple", "dataclass"}:
                for field in node.body:
                    if isinstance(field, ast.AnnAssign):
                        field_name = field.target.id
                        field_qualname = f"{qualname}.{field_name}"
                        self.symbols.append(
                            Symbol(
                                name=field_name,
                                qualname=field_qualname,
                                type="attribute",
                                documentation=None,
                                sourcePath=str(self.source),
                                range=rangeFromNode(node),
                            )
                        )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        qualname = (
            f"{self.moduleName}.{node.name}"
            if self.parentName == ""
            else f"{self.parentName}.{node.name}"
        )
        self.symbols.append(
            Symbol(
                name=node.name,
                qualname=qualname,
                type="function",
                documentation=ast.get_docstring(node),
                sourcePath=str(self.source),
                range=rangeFromNode(node),
            )
        )
        visitor = SymbolVisitor(self.source, self.moduleName, qualname)
        visitor.visit(node.args)
        self.symbols.extend(visitor.symbols)


def iterSymbols(source: Path, moduleName: str) -> Iterator[Symbol]:
    """Iterates throught the symbols"""
    with source.open("rt", encoding="utf-8") as f:
        root = ast.parse(f.read(), str(source))

    visitor = SymbolVisitor(source, moduleName)
    visitor.visit(root)

    return iter(visitor.symbols)


def lineOffsets(content: str) -> Iterator[int]:
    offset = 0
    for line in content.split("\n"):
        yield offset + (n := len(line) + 1)
        offset += n


def offsetFromRange(lines: list[int], range: TextRange) -> tuple[int, int]:
    return (
        lines[range.startLine] + range.startColumn,
        lines[-1 if range.endLine is None else range.endLine] + (range.endColumn or 0),
    )


chunks = []
source_path = Path(__file__)
source_text = source_path.read_text()
offsets = list(lineOffsets(source_text))
offset: int = 0
# print("<html><body>")
for sym in sorted(
    iterSymbols(source_path, "example"),
    key=lambda _: _.range.startLine + _.range.startColumn,
):
    s, e = offsetFromRange(offsets, sym.range)
    print(sym, repr(source_text[s:e][:100]))
    # if s > offset:
    #     print(f"<pre>{escape(source_text[offset:s])}</pre>")
    # print(f"<h3><a name='{sym.qualname}'>{sym.qualname}:{sym.type} {s=} {e=}</a></h3>")
    # print(f"<pre>{escape(source_text[s:e])}</pre>")
# offset = e
# if offset < len(source_text):
#     print(f"<pre>{escape(source_text[offset:])}</pre>")
# print("</body></html>")
# EOF
