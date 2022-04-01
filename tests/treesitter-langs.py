from tree_sitter import Language, Parser
from pathlib import Path
import os

REPOS = Path(__file__).parent.parent / ".deps/src"
BUILD = Path(__file__).parent.parent / ".build"

LANGS = os.getenv("TREESITTER_LANGS", "python javascript").split()

if not BUILD.exists():
    BUILD.mkdir()

Language.build_library(
    # Store the library in the `build` directory
    str(BUILD / "treesitter-languages.so"),
    # Include one or more languages
    [str(REPOS / f"tree-sitter-{lang}") for lang in LANGS],
)

langs = {lang: Language(BUILD / "treesitter-languages.so", lang) for lang in LANGS}

print(f"... OK! {langs}")

# EOF
