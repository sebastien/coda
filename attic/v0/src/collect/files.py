from typing import NamedTuple, Generator, Iterator
from pathlib import Path
import os
from fnmatch import fnmatch
from ..utils.treematrix import TreeMatrix


class File(NamedTuple):
    name: str
    ext: str
    language: str | None = None


class Entry(NamedTuple):
    id: str
    parent: str
    name: str
    file: File | None = None


class Files:
    @staticmethod
    def Walk(
        path: str | Path,
        *,
        followLinks: bool = False,
    ) -> Generator[Path, bool, None]:
        root_path = (path if isinstance(path, Path) else Path(path)).absolute()
        for base, dirs, files in os.walk(root_path):
            for f in files:
                yield (Path(base) / f).relative_to(root_path)

    @staticmethod
    def Filter(
        stream: Iterator[Path],
        *,
        includes: list[str] | None = None,
        excludes: list[str] | None = None,
    ) -> Iterator[Path]:
        for p in stream:
            matches: bool = True
            if includes:
                matches = False
                for _ in includes:
                    if fnmatch(p.name, _):
                        matches = True
                        break
            if matches and excludes:
                for _ in excludes:
                    if fnmatch(p.name, _):
                        matches = False
                        break
            if matches:
                yield p

    @staticmethod
    def Catalogue(
        stream: Iterator[Path],
    ) -> TreeMatrix[str, Entry]:
        res: TreeMatrix[str, Entry] = TreeMatrix()
        for path in stream:
            p = str(path.parent)
            f = Entry(
                id=str(path),
                name=str(path.name),
                parent=p,
                file=File(
                    name=str(path.stem),
                    ext=str(path.suffix),
                ),
            )
            res.register(f.id, f, f.parent)
        # We merge in the parents
        for p in {_ for _ in res.parents.values() if _ not in res.nodes}:
            res.register(
                p,
                Entry(id=p, name=os.path.basename(p), parent=os.path.dirname(p)),
                parent=os.path.dirname(p),
            )
        # The only nodes that remain without parents are the roots
        for k in {k for k, v in res.parents.items() if v not in res.nodes}:
            del res.parents[k]
        return res


if __name__ == "__main__":
    from ..utils.json import asJSON

    cat = Files.Catalogue(
        Files.Filter(Files.Walk("src"), includes=["*.py", "*.sh", "*.js"])
    )
    for r in cat.roots():
        with open("research/data/files.json", "wt") as f:
            f.write(asJSON([cat.asNode(r)]))


# EOF
