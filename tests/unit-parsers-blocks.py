from coda.parsers.blocks import Block, Fragment, BlockParser

EXAMPLE = """\
Code
# --
# Block
# Block
Code
Code
Code
# --
# Block
Code
"""

EXPECTED = [
    Block(
        fragment=Fragment(path=None, offset=0, length=5, line=0, column=0, text=None)
    ),
    Block(
        fragment=Fragment(path=None, offset=5, length=21, line=1, column=0, text=None)
    ),
    Block(
        fragment=Fragment(path=None, offset=26, length=15, line=4, column=0, text=None)
    ),
    Block(
        fragment=Fragment(path=None, offset=41, length=13, line=7, column=0, text=None)
    ),
    Block(
        fragment=Fragment(path=None, offset=54, length=6, line=9, column=0, text=None)
    ),
]

for i, b in enumerate(
    BlockParser.Blocks(
        BlockParser.BlockLines(
            BlockParser.Lines(EXAMPLE.split("\n"), eol=False, path=None)
        )
    )
):
    assert b == EXPECTED[i]
# EOF
