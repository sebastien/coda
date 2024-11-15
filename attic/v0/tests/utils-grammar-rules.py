from coda.utils.grammar import grammar
from coda.utils.statemachine import StateMachine
from harness import test, same, fail, out, hlo, harness

hlo("Creation of single state machinne rules grammar()")


def check(rules: dict[str, str], input: str, *expected: tuple[str, str]):
    """Checkes that the input produces the output with the given rules"""
    i: int = 0
    parser = StateMachine(grammar(rules))

    for match in parser.run(tokens := input.split()):
        name = match.name
        if i >= len(expected):
            return fail(
                f"Expected {len(expected)} got {i+1}, extra={match} input={repr(input)}"
            )
        if not same(
            (match.name, " ".join(tokens[match.start : match.end])), expected[i]
        ):
            out(f" …  {parser.pretty()}")
        i += 1
    if i < len(expected):
        fail(f"Expected {len(expected)} got {i}, missing: {expected[i:]}")
        out(f" …  {parser}")


with harness(stopOnFail=True):

    with test("Grammar ONE combinator"):
        check(
            {"M": "T"},
            "T",
            ("M", "T"),
        )
        check(
            {"M": "T"},
            "T T",
            ("M", "T"),
            ("M", "T"),
        )

    with test("Grammar OPTIONALLY ONE combinator"):
        check(
            {"M": "T?"},
            "T",
            ("M", "T"),
        )

        # The match should be empty as T matches anything.
        check(
            {"M": "T?"},
            "A",
            ("M", ""),
        )

        # The match should be empty as T matches anything.
        check(
            {"M": "T?"},
            "T T",
            ("M", "T"),
            ("M", "T"),
        )

    with test("Grammar MANY combinator"):
        check(
            {"M": "T+"},
            "T",
            ("M", "T"),
        )
        check(
            {"M": "T+"},
            "T T",
            ("M", "T T"),
        )
        for t in ["T", "T T", "T T T", "T T T T T T T"]:
            check({"M": "T+"}, t, ("M", t))

    with test("Grammar OPTIONALLY MANY combinator"):
        check(
            {"M": "T*"},
            "A",
            ("M", ""),
        )

        for t in ["T", "T T", "T T T", "T T T T T T T"]:
            check({"M": "T+"}, t, ("M", t))

# EOF
