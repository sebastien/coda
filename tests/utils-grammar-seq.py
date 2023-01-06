from coda.utils.grammar import grammar
from coda.utils.statemachine import StateMachine
from harness import test, same, fail, out, hlo

hlo("Creation of single state machinne rules")


def check(rules: dict[str, str], input: list[str], expected: list[list[str]]):
    """Checkes that the input produces the output with the given rules"""
    i: int = 0
    parser = StateMachine(grammar(rules))

    for match in parser.run(input):
        name = match.name
        if not same([match.name] + input[match.start : match.end], expected[i]):
            out(f" …  {parser}")
        i += 1
    if i < len(expected):
        fail(f"Expected {len(expected)} got {i}, missing: {expected[i:]}")
        out(f" …  {parser}")


if True:
    with test("Grammar ONE combinator"):
        check(
            {"M": "T"},
            ["T"],
            [
                ["M", "T"],
            ],
        )
        check(
            {"M": "T"},
            ["T", "T"],
            [
                ["M", "T"],
                ["M", "T"],
            ],
        )

    with test("Grammar OPTIONALLY ONE combinator"):
        check(
            {"M": "T?"},
            ["T"],
            [
                ["M", "T"],
            ],
        )
        # The match should be empty as T matches anything.
        check(
            {"M": "T?"},
            ["A"],
            [
                ["M"],
            ],
        )

    with test("Grammar MANY combinator"):
        for t in (_.split() for _ in ["T", "T T", "T T T", "T T T T T T T"]):
            check(
                {"M": "T+"},
                t,
                [
                    ["M"] + t,
                ],
            )

    with test("Grammar OPTIONALLY MANY combinator"):
        check(
            {"M": "T*"},
            ["A"],
            [
                ["M"],
            ],
        )
        for t in (_.split() for _ in ["T", "T T", "T T T", "T T T T T T T"]):
            check(
                {"M": "T+"},
                t,
                [
                    ["M"] + t,
                ],
            )

# EOF
