from coda.utils.grammar import grammar, seq
from coda.utils.statemachine import StateMachine, pretty
from harness import test, same, fail, out, hlo
import re

hlo("Exercises the translation of seq() into transitions")


def check(tokens: str, *expected: str) -> bool:
    """Takes a list of expected transitions like `EVENT:ORIGIN->TARGET[STATE]`"""
    transitions = seq(*tokens.split())
    steps: list[str] = []
    for origin, states in transitions.items():
        for event, transition in states.items():
            steps.append(
                f"{event}:{origin}->{transition.target}{str(transition.status).split('.')[1][0]}"
            )
    for i, t in enumerate(expected):
        if not same(steps[i], t):
            out(f" …  Step {i+1}/{len(transitions)} failed")
            for j, step in enumerate(steps):
                if step == expected[j]:
                    out(f" …  [{j:2d}] {step}")
                else:
                    out(f" ~  [{j:2d}] {step} expected={expected[j]}")
            return False
    return True


with test("Single token sequences"):
    check("block", "block:0->1C", "*:1->0E")
    check("block?", "block:0->1C", "*:0->0E", "*:1->0E")
    check("block+", "block:0->1C", "block:1->1C", "*:1->0E")
    check("block*", "block:0->1C", "*:0->0E", "block:1->1C", "*:1->0E")

with test("Double token sequences"):
    check("block comment", "block:0->1P", "comment:1->2C", "*:2->0E")
    check("block comment?", "block:0->1P", "comment:1->2C", "*:1->0E", "*:2->0E")
    check("block comment+", "block:0->1P", "comment:1->2C", "comment:2->2C", "*:2->0E")
    check("block comment*", "block:0->1P", "comment:1->2C", "*:1->0E")

# EOF
