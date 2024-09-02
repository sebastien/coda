from coda.parser import blocks
from harness import hlo, test, same, fail

hlo("Parsing Python coda blocks property")


def check(*inputs: tuple[str, str]):
    """Takes `inputs=(MatchName, MatchText)` like `("Block, "# --\n")`),
    and validates that the parsed text (concat of all the second items of the inputs)
    is parsed as the inputs."""
    for i, b in enumerate(blocks("\n".join(t for _, t in inputs))):
        if i >= len(inputs):
            return fail(
                f"Too many parsed blocks, expected {len(inputs)}, got {i + 1}: {b}"
            )
        expected = inputs[i]
        got = (b.type, b.text)
        if not same(got, expected):
            # break
            pass


# with test("Single block"):
#     check(("Block", "# --\n"))
#
# with test("BUG Double call to check"):
#     check(("Block", "# --\n"))
#     check(("Block", "# --\n"))

with test("Mulitline block"):
    check(
        ("Block", "# --\n# BLA0\n# BLA1"),
    )

# EOF
