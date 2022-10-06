from coda.reparser import Marks, Block, text, iterMarks, compile

BLOCKS = """
# --
# Block 1
Line 1

# --
# Block 2.1
# Block 2.2
Line 2
Line 3
"""

# with grammar():
# BlockStart = atom("")
# Comment = atom("")
# Block =

g = compile(
    Marks(
        {
            "block": r"^([ \t]*)#[ ]+--[ ]*\n",
            "comment": r"^([ \t]*)#.*$",
        },
        {},
    )
)
for m in iterMarks(g, BLOCKS):
    print(m)
# EOF
