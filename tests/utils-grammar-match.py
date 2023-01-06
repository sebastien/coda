from coda.utils.grammar import grammar
from harness import hlo, test

hlo("Checks if tokens trigger rules as expected")

parser = grammar({"Sep": "sep+"})

for m in parser.run(["sep", "sep", "sep"]):
    print(m)

parser = grammar(
    {
        "Block": "blockStart comment*",
        "Comment": "comment+",
        "Sep": "sep+",
        "Code": "_+",
    }
)

for m in parser.run(["sep", "sep", "sep"]):
    print(m)
