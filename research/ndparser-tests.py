from coda.reparser import Marks, Block, compile, marks, text
from grammar import
from typing import Optional
import re

# --
# First test is to parse blocks
if False:
    print("=== TEST ND Block parsing text")

    BLOCKS = """\
    BLOCK 1A
    BLOCK 1B

    BLOCK 2A

    BLOCK 3A
    BLOCK 3C


    BLOCK 4A"""

    BlockSeparator = re.compile("\n([ \t]*\n)+")
    blocks = marks(BLOCKS, BlockSeparator)
    print(blocks)
    print("EOK")

# --
# Second test is to parse inlines
if True:
    print("=== TEST ND Inline parsing test")
    INLINES = """\
    *emphasis* _term_ [link](url) <url> `code`.
    """

    def inline(s: str, e: Optional[str] = None):
        return Block(start=text(s), end=text(e or s))

    nd_marks = Marks(
        {
            "block": r"\n([ \t]*\n)+",
            "emphasis": text("*"),
            "code": text("`"),
            "term": text("_"),
            "escape": text("\\"),
        },
        {
            "ref": inline("[", "]"),
            "url": inline("<", ">"),
        },
    )
    for m in marks("*_`code`_*", nd_marks):
        print("M", m)
# EOF
