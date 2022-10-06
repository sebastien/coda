with Literate := grammar():
    BlockStart = atom(r"^([ \t]*)#[ ]+--[ ]*\n")
    Comment = atom(r"^([ \t]*)#.*$")
    Block = BlockStart & (Comment * Many)
