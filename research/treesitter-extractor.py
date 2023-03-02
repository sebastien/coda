from tree_sitter import Language, Node, Tree, Parser
from typing import Optional, ClassVar, NamedTuple
from pathlib import Path
import re, sys
import subprocess

out = sys.stdout.write

# --
# This notebook shows how to extract symbols (declaration and reference)
# from tree sitter.


# --
# ## Data model


class Fragment(NamedTuple):
    start: int
    end: int


class Symbol:
    pass


class SymbolDeclaration:
    pass


class SymbolReference:
    pass


# --
# ## TreeSiter


class TreeSitter:
    PATH_BASE: ClassVar[Path] = Path(__file__).parent
    PATH_REPOS: ClassVar[Path] = PATH_BASE / "deps"
    RE_LANGUAGE: ClassVar[re.Pattern] = re.compile("^[a-z-]+$")

    @classmethod
    def Install(cls, lang: str) -> Path:
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


if __name__ == "__main__":
    langs = TreeSitter.Languages("python")

    # Usage:
    with open(__file__, "rb") as f:
        py = langs["python"]
        parser: Parser = Parser()
        text: bytes = f.read()
        parser.set_language(py)
        tree = parser.parse(text)
        lines = text.split(b"\n")
        # --
        # These are Tree Sitter queries
        for q in (
            "(function_definition name: (identifier) @name)",
            "(class_definition name: (identifier) @name)",
            "(parameter name: (identifier) @name)",
            # "(attribute name: (identifier) @name)",  # Attribute reference
            # "(object name: (identifier) @name)",  # Object reference
            "(assignment left: (identifier) @name )",  # Object reference
        ):
            print("Q", q)
            query = py.query(q)
            res = query.captures(tree.root_node)
            for match, var in res:
                i, oi = match.start_point
                j, oj = match.end_point
                if i == j:
                    t = lines[i][oi:oj]
                else:
                    t = lines[i + 1 : j - 1]
                    t.insert(0, lines[i][oi:])
                    t.append(lines[j][:oj])

                print(match.start_point, match.end_point, t)


# EOF
