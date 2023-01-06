from coda.parser import blocks
from harness import hlo, test, same, fail

hlo("Parsing Python coda blocks property")


def check(*inputs: tuple[str, str]):
    for i, b in enumerate(blocks("\n".join(t for _, t in inputs))):
        if i >= len(inputs):
            return fail(
                f"Too many parsed blocks, expected {len(inputs)}, got {i + 1}: {b}"
            )
        expected = inputs[i]
        got = (b.type, b.text)
        if not same(got, expected):
            break


with test("Single block"):
    check(("Block", "# --\n"))

with test("BUG Double call to check"):
    check(("Block", "# --\n"))
    check(("Block", "# --\n"))
# check(("Block", "# --\nBLA0\nBLA1"), ("Comment", "#CmA0\n#CA1"), ("Code", "CoA0\nCoA1"))

# EOF
