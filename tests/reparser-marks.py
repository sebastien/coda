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
