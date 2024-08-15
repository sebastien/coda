from typing import NamedTuple, Iterator
from pathlib import Path
from enum import Enum
import subprocess
import glob
import json
import re


def asPrimitive(value):
    if isinstance(value, Enum):
        return value.name
    elif isinstance(value, tuple) and hasattr(value, "_asdict"):  # NamedTuple
        return asPrimitive(value._asdict())
    elif isinstance(value, Path):
        return str(value)
    elif isinstance(value, list):
        return [asPrimitive(_) for _ in value]
    elif isinstance(value, tuple):
        return tuple(*(asPrimitive(_) for _ in value))
    elif isinstance(value, dict):
        return {k: asPrimitive(v) for k, v in value.items()}
    else:
        return value


class Fragment(NamedTuple):
    path: Path
    offset: int
    length: int
    line: int
    column: int
    text: str | None = None


class SymbolType(Enum):
    ImportedInternal = "I"
    ImportedExternal = "Y"
    Class = "c"
    Function = "f"
    Module = "i"
    Member = "m"
    Variable = "v"
    Type = "t"


class TagEntry(NamedTuple):
    """Represents a single tag entry in a ctags/etags file."""

    symbol: str
    type: SymbolType
    fragment: list[Fragment]


#
#     name: str  # The identifier of the code element
#     location: str  # File path and line number
#     tagType: str  # Kind of element (e.g., "function", "class")
#     additionalInfo: Optional[str] = None  # Extra details (scope, attributes, etc.)
#
#
# class TagFile(NamedTuple):
#     """Represents a ctags/etags file containing a collection of tags."""
#
#     tags: List[TagEntry]
#     filePath: str


def parseCTagsFile(path: str | Path) -> Iterator[TagEntry]:
    with open(path, "rt") as f:
        yield from (_ for _ in parseCTags((_ for _ in f.readlines()), path=path))


# TODO: This will likely slow things down as the files are read for
# every single symbol.
def findOccurences(
    path: Path, pattern: str, *, base: Path | None = None
) -> Iterator[Fragment]:
    pattern = pattern.replace("\\\\/", "/")
    offset: int = 0
    rel_path = path.relative_to(base) if base else path
    if pattern.startswith("/^") and pattern.endswith('$/;"'):
        pat = pattern[2:-4]
        with open(path, "rt") as f:
            for i, line in enumerate(f.readlines()):
                if line.strip("\n") == pat:
                    yield Fragment(
                        rel_path, offset, len(pat), line=i, column=0, text=pat
                    )
                offset += len(line)
    else:
        with open(path, "rt") as f:
            for i, line in enumerate(f.readlines()):
                j = line.find(pattern)
                if j >= 0:
                    yield Fragment(
                        rel_path,
                        offset + j,
                        len(pattern),
                        line=i,
                        column=j,
                        text=pattern,
                    )
                offset += len(line)


def parseCTags(
    stream: Iterator[str], path: str | Path | None = None
) -> Iterator[TagEntry]:
    """Parses a ctags/etags file and returns a TagFile object."""
    base_path = (
        (Path.cwd() if path is None else Path(path) if path is str else path)
        .absolute()
        .parent
    )
    for i, line in enumerate(stream):
        if line.startswith("!"):
            # Declaration
            # !_TAG_EXTRA_DESCRIPTION	anonymous	/Include tags for non-named objects like lambda/
            continue

        symbol, path, pattern = line.split("\t", 2)
        pattern, t = pattern.strip("\n").rsplit("\t", 1)
        # TODO: We could source the location from the path and regexp
        stype: SymbolType | None = next((_ for _ in SymbolType if _.value == t), None)
        # TODO: Should probably warn if there's a problem
        yield TagEntry(
            symbol,
            stype,
            list(findOccurences(base_path / path, pattern, base=base_path)),
        )
        # Meta information is going to be like
        # [class:PARENT?, typeref:RETURNS?]
        # ```
        # ['typeref:typename:TJSON\n']
        # ['class:Node\n']
        # ['class:Node', 'typeref:typename:list[Any]\n']
        # ['class:TreeMatrix', 'typeref:typename:Iterator[T]\n']
        # ['typeref:typename:Iterable[str]\n']
        # ['class:Node', "typeref:typename:'Node[T]'\n"]
        # ['member:Factory.__getattr__', 'typeref:typename:Node\tfile:\n']
        # ```


def makeCTags(paths: list[str]) -> str:
    """Generates ctags content for a list of file paths (including globs)."""
    expanded_paths = []
    for path in paths:
        expanded_paths.extend(glob.glob(path, recursive=True))  # Expand glob patterns

    result = subprocess.run(
        ["ctags", "-R"] + expanded_paths, capture_output=True, text=True, check=True
    )

    if result.returncode == 0:
        return list(parseCTagsFile("tags"))
    else:
        raise RuntimeError("ctags execution failed with error:\n" + result.stderr)


# Example usage
if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    if not args:
        paths = ["*.py", "src/**/*.py"]
        ctags_content = makeCTags(paths)
        print(ctags_content)
    else:
        entries = []
        with open(path := Path(args[0])) as f:
            for t in parseCTags(f.readlines(), path):
                entries.append(asPrimitive(t))

        print(json.dumps(entries))

#
# # Example usage:
# tag1 = TagEntry("calculate_total", "math_utils.py:5", "function")
# tag2 = TagEntry("PI", "constants.py:2", "variable", "constant")
# tag_file = TagFile([tag1, tag2], "tags")
#
# print(tag_file)

# EOF
