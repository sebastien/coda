from tree_sitter import Language, Node, Tree, Parser
from typing import Optional, ClassVar, NamedTuple
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from enum import Enum
import re, sys
import subprocess

out = sys.stdout.write

# --
# This notebook shows how to extract symbols (declaration and reference)
# from tree sitter.


# --
# ## Data model


class Fragment:
    text: bytes
    start: int
    end: int

    def __init__(self, text: bytes, start: int, end: int):
        self.text = text
        self.start = start
        self.end = end
        self.value = str(self.text[self.start : self.end], "utf8")

    def __repr__(self):
        return repr(self.value)


@dataclass
class Symbol:
    name: str
    qualname: Optional[str] = None
    mentions: list["Mention"] = field(default_factory=list)


class MentionType(Enum):
    DEFINITION = "def"
    REFERENCE = "ref"
    ASSIGNMENT = "asn"


@dataclass
class SymbolMention:
    type: str
    symbol: Symbol
    location: Fragment


# --
# ## TreeSitter


class TreeSitter:
    """A simple wrapper that automatically downloads and compiles tree sitter language
    modules."""

    PATH_BASE: ClassVar[Path] = Path(__file__).parent.parent
    PATH_REPOS: ClassVar[Path] = PATH_BASE / "deps"
    RE_LANGUAGE: ClassVar[re.Pattern] = re.compile("^[a-z-]+$")

    @classmethod
    def Install(cls, lang: str) -> Path:
        """Installs the language `lang` and returns the path where the repository
        is located."""
        if not cls.RE_LANGUAGE.match(lang):
            raise ValueError(f"Unsupported language format: {lang}")
        elif not (repo := cls.PATH_REPOS / f"tree-sitter-{lang}").exists():
            out(">>> STEP Checking out language: lang={lang} path={repo}\n")
            out("```\n")
            git_url = f"git@github.com:tree-sitter/tree-sitter-{lang}.git"
            res = subprocess.run(
                ["git", "clone", "--depth=1", git_url, str(repo)],
                check=True,
            )
            out("```\n")
            if res.returncode != 0:
                raise RuntimeError("Could not clone repository {git_url}")
            else:
                out("<<< OK\n")
        return repo

    @classmethod
    def Languages(
        cls,
        *languages: str,
        path: Optional[Path] = None,
    ) -> dict[str, Language]:
        """Returns a map of available TreeSitter languages"""
        lib_path = str(path or cls.PATH_BASE / "treesitter-languages.so")
        Language.build_library(
            # Store the library in the `build` directory
            str(lib_path),
            [str(cls.Install(_)) for _ in languages],
        )
        return {lang: Language(lib_path, lang) for lang in languages}


class TreeSitterText:
    def __init__(self, text: bytes):
        self.value: bytes = text
        self.lines: list[bytes] = text.split(b"\n")
        self.offsets: list[int] = []
        o: int = 0
        for l in self.lines:
            self.offsets.append(o)
            o += len(l) + 1

    def fragment(self, start: tuple[int, int], end: tuple[int, int]) -> Fragment:
        sl, so = start
        el, eo = end
        return Fragment(self.value, self.offsets[sl] + so, self.offsets[el] + eo)


if __name__ == "__main__":
    langs = TreeSitter.Languages("python")

    symbols: dict[str, Symbol] = {}

    def ensure_symbol(name: str):
        if name not in symbols:
            symbols[name] = Symbol(name)
        return symbols[name]

    # Usage:
    with open(__file__, "rb") as f:
        py = langs["python"]
        parser: Parser = Parser()
        text = TreeSitterText(f.read())
        parser.set_language(py)
        tree = parser.parse(text.value)
        # --
        # These are Tree Sitter queries
        for t, q in (
            ("def", "(function_definition name: (identifier) @name)"),
            ("def", "(class_definition name: (identifier) @name)"),
            ("def", "(parameter name: (identifier) @name)"),
            # ("def",  "(attribute name: (identifier) @name)"),  # Attribute reference
            # ("def",  "(object name: (identifier) @name)"),  # Object reference
            ("asn", "(assignment left: (identifier) @name )"),  # Object reference
        ):
            query = py.query(q)
            res = query.captures(tree.root_node)
            for match, var in res:
                # i, oi = match.start_point
                # j, oj = match.end_point
                # if i == j:
                #     t = lines[i][oi:oj]
                # else:
                #     t = lines[i + 1 : j - 1]
                #     t.insert(0, lines[i][oi:])
                #     t.append(lines[j][:oj])

                frag = text.fragment(match.start_point, match.end_point)
                name = frag.value

                # TODO: We need to identify the scope
                sym = ensure_symbol(name)
                mention = SymbolMention(t, sym, frag)
                sym.mentions.append(mention)
    for s in symbols.values():
        print(s)


# EOF
