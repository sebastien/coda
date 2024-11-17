from typing import NamedTuple, Iterator
from pathlib import Path
from subprocess import run
from enum import Enum
from glob import glob

from ..model import Fragment
from ..utils.export import asPrimitive


class TagSymbolType(Enum):
    ImportedInternal = "I"
    ImportedExternal = "Y"
    Const = "C"
    Class = "c"
    Function = "f"
    Module = "i"
    Member = "m"
    Variable = "v"
    Type = "t"


class TagEntry(NamedTuple):
    """Represents a single tag entry in a ctags/etags file."""

    symbol: str
    type: TagSymbolType | None
    fragment: list[Fragment]


class Tags:

    # TODO: Support tag file location
    @classmethod
    def Make(cls, *paths: str | Path) -> Iterator[TagEntry]:
        """Generates ctags content for a list of file paths (including globs)."""
        expanded_paths = []
        for path in paths:
            expanded_paths.extend(
                glob(str(path), recursive=True)
            )  # Expand glob patterns

        result = run(
            ["ctags", "-R"] + [str(_) for _ in expanded_paths],
            capture_output=True,
            text=True,
            check=True,
        )

        if result.returncode == 0:
            for _ in cls.ParseFile("tags"):
                yield _
        else:
            raise RuntimeError("ctags execution failed with error:\n" + result.stderr)

    @classmethod
    def ParseFile(cls, path: str | Path) -> Iterator[TagEntry]:
        """Parses the tags in the given tags file."""
        with open(path, "rt") as f:
            yield from (_ for _ in cls.Parse((_ for _ in f.readlines()), path=path))

    @staticmethod
    def Parse(stream: Iterator[str], *, path: str | Path | None = None):
        """Parses a ctags/etags file and returns a TagFile object."""
        base_path: Path = (
            (
                Path.cwd()
                if path is None
                else Path(path) if isinstance(path, str) else path
            )
            .absolute()
            .parent
        )
        for line in stream:
            if line.startswith("!"):
                # Declaration
                # !_TAG_EXTRA_DESCRIPTION	anonymous	/Include tags for non-named objects like lambda/
                continue

            symbol, path, pattern = line.split("\t", 2)
            pattern, t = pattern.strip("\n").rsplit("\t", 1)
            # TODO: We could source the location from the path and regexp
            # TODO: We sometimes have extra info, so we should probably split by \t/^ and then /;"
            # ASSETS	./.deps/src/build-kit/src/py/buildkit/commands/package.py	/^    ASSETS = {$/;"	v	class:Package
            stype: TagSymbolType | None = next(
                (_ for _ in TagSymbolType if _.value == t), None
            )
            # TODO: Should probably warn if there's a problem
            yield TagEntry(
                symbol,
                stype,
                list(Fragment.Find(base_path / path, pattern, base=base_path)),
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


if __name__ == "__main__":
    import sys, json

    args = sys.argv[1:]
    if not args:
        paths = ["*.*", "src/**/*.*"]
        for _ in Tags.Make(*paths):
            print(_)
    else:
        entries = []
        for t in Tags.ParseFile(args[0]):
            entries.append(asPrimitive(t))

        print(json.dumps(entries))

# EOF
