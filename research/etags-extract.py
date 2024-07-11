from typing import NamedTuple, Iterator
from pathlib import Path
from enum import Enum
import subprocess
import glob
import re


class SymbolType(Enum):
    ImportedInternal = "I"
    ImportedExternal = "Y"
    Class = "c"
    Function = "f"
    Module = "i"
    Member = "m"
    Variable = "v"


class TagEntry(NamedTuple):
    """Represents a single tag entry in a ctags/etags file."""


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
        return (_ for _ in parseCTags(_ for _ in f.readlines()))


def parseCTags(stream: Iterator[str]) -> Iterator[TagEntry]:
    """Parses a ctags/etags file and returns a TagFile object."""
    for line in stream:
        items = line.split("\t", 5)
        if not items:
            continue
        if items[0].startswith("!"):
            # ['!_TAG_KIND_DESCRIPTION!Python', 'Y,unknown', '/name referring a class\\/variable\\/function\\/module defined in other module/\n']
            pass
        else:
            symbol, path, regexp = items[0:3]
            # TODO: We could source the location from the path and regexp
            stype: SymbolType | None = next(
                (_ for _ in SymbolType if _.value == items[3]), None
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

            print("META", items[4:])


def makeCTags(paths: list[str]) -> str:
    """Generates ctags content for a list of file paths (including globs)."""
    expanded_paths = []
    for path in paths:
        expanded_paths.extend(glob.glob(path, recursive=True))  # Expand glob patterns

    print(expanded_paths)
    result = subprocess.run(
        ["ctags", "-R"] + expanded_paths, capture_output=True, text=True, check=True
    )

    if result.returncode == 0:
        return list(parseCTagsFile("tags"))
    else:
        raise RuntimeError("ctags execution failed with error:\n" + result.stderr)


# Example usage
paths = ["*.py", "src/**/*.py"]
ctags_content = makeCTags(paths)
print(ctags_content)

#
# # Example usage:
# tag1 = TagEntry("calculate_total", "math_utils.py:5", "function")
# tag2 = TagEntry("PI", "constants.py:2", "variable", "constant")
# tag_file = TagFile([tag1, tag2], "tags")
#
# print(tag_file)

# EOF
