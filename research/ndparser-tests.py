import re
from coda.reparser import marks

print("=== TEST: ND Parser Test")

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
