# --
# # Nota Parser
#
# I know this one is going to be big, it's the parsing of Nota, a Markdown derived
# format designed for semantic note taking.

import re

# --
# ## Parsing primitivives

# These are the tokens that come in pair (for the most part)
Duals = [
    ("[", "]"),
    ("{", "}"),
    ("(", ")"),
    ('"', '"'),
    ("'", "'"),
]

ND = "*"
URL = "*"

# Inlines
class Inline:
    def __init__(self, *tokens: str):
        pass


# Here we want to match anything like `_*`code`*_`
Emphasis = Inline("*", ND, "*")
Term = Inline("_", ND, "_")
Code = Inline("`", ND, "`")
Link = Inline("[", ND, "]", "(", URL, ")")

UnorderedListItem = " - "
OrderedListItem = "1) "


# Blocks


class Block:
    def __init__(self, start: str, end: Optional[str] = None):
        self.start = start
        self.end = end


# This is an explicit start/end block
Pre = Block(
    start="```",
    end="```",
)

# This is an implicit end block, ie the next matching block will
# take over
UnorderedListItem = Block(start=(Indent, "-"))

# --
# ## Parsing passes
