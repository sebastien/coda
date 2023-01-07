from coda.utils.grammar import grammar
from coda.utils.statemachine import StateMachine, CompletionEvent, iterPretty
from harness import hlo, test, same, fail, out

hlo("Checks if tokens trigger rules as expected")


def check(rules: dict[str, str], *inputs: tuple[str, str]) -> bool:
    """Takes `inputs=(MatchName, MatchText)` like `("Block, "# --\n")`),
    and validates that the parsed text (concat of all the second items of the inputs)
    is parsed as the inputs."""
    j: int = 0
    machine = StateMachine(grammar(rules))
    tokens: list[str] = []
    for _, t in inputs:
        tokens += t.split()
    for i, event in enumerate(machine.run(_ for _ in tokens)):
        print("EVENT", event)
        if i >= len(inputs):
            return fail(
                f"Too many parsed blocks, expected {len(inputs)}, got {i + 1}: {event}"
            )
        # start = event.start if event.start < len(markers) else -1
        # end = event.end if event.end < len(markers) else tokens[-1]
        # return (event.name or "#text", tokens[start:end])

        expected = inputs[i]
        got = (event.name, " ".join(tokens[event.start : event.end]))
        if same(got, expected):
            j += 1
        else:
            break
    if j != len(inputs):
        fail(f"Expected {len(inputs)} match, got {j}")
        out(f" …  {machine}")
        for line in iterPretty(machine.transitions):
            out(f" …  {line}")
    else:
        return False


with test("One rule grammar"):
    check({"Sep": "sep+"}, ("Sep", "sep"))
    check({"Sep": "sep+"}, ("Sep", "sep sep"))
    check({"Sep": "sep+"}, ("Sep", "sep sep sep"))

with test("One rule, two tokens"):
    check({"Block": "block comment"}, ("Block", "block comment"))
    check(g, ("Block", "block"), ("Code", "code"))
    check(g, ("Block", "block comment"), ("Code", "code"))


# EOF
