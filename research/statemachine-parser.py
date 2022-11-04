from coda.reparser import Marks, marks
from pathlib import Path
from statemachine import StateMachine, Transition, Status
from typing import Optional

# --
# The next step after our `statemachine` notebook is to integrate the
# statemachines with our regular expression based parser.


def seq(*matches: str) -> dict[int, dict[str, Transition]]:
    """Takes a list of token names suffixed by a cardinality `[?+*]` and
    generates a corresponding mapping of state machine states and their
    map of transitions."""
    res: dict[int, dict[str, Transition]] = {0: {}}
    i: int = 0
    j: int = 0
    n: int = len(matches)
    # --
    # We iterate on each match
    while i < n:
        match = matches[i]
        name: str = ""
        card: str = ""
        is_last: bool = i + 1 >= n
        print(f"i={i} is_last={is_last} matches={matches}")
        next_name: Optional[str] = matches[i + 1] if not is_last else None
        # --
        # First step, we extract the cardinality
        if (card := match[-1]) in "?+*":
            name = match[:-1]
        else:
            name = match
            card = ""
        # --
        # We get the state machine, and its transitions. The
        # --
        # Now, based on the cardinality we add specific transitions
        match card:
            case "":
                # --
                # If it's a single match, so when we match this step, we go
                res[j] = {
                    name: Transition(0, Status.End) if is_last else Transition(j + 1)
                }
                j += 1
            case "?":
                res[j] = {
                    name: Transition(0, Status.End) if is_last else Transition(j + 1),
                    "*": Transition(0, Status.End) if is_last else Transition(j + 1),
                }
                j += 1
            case "+":
                # We start with a transition that matches the `name`
                res[j] = {
                    name: Transition(j + 1, Status.Start),
                }
                # Then the next step can match `name` again, or end then.
                res[j + 1] = {
                    name: Transition(0, Status.Complete)
                    if is_last
                    else Transition(j + 1),
                    "*": Transition(0, Status.End) if is_last else Transition(j + 1),
                }
                j += 2
            case "*":
                # We start with a transition that matches the `name`
                res[j] = {
                    name: Transition(j + 1, Status.Complete),
                    "*": Transition(0, Status.End) if is_last else Transition(j + 1),
                }
                # Then the next step can match `name` again, or end then.
                res[j + 1] = {
                    name: Transition(j, Status.Complete)
                    if is_last
                    else Transition(j + 1),
                    "*": Transition(0, Status.End) if is_last else Transition(j + 1),
                }
                j += 2
        i += 1
    return res


print("=== TEST seq: defining a sequence of transitions")
res = seq("commentStart", "commentLine+")
print(res)
machine = StateMachine(res, name="Comments")
print(machine)
print("--- OK")
# def grammar(rules: dict[str, dict[str, Transition]]):
#     return None
#
#
# # --
# # We define the tokens we care about
# python_tokens: Marks = Marks(
#     {
#         "commentStart": r"#\s*\-\-\s*\n",
#         "comment": r"#(?P<text>[^\n]*)\n",
#     },
#     {},
# )
#
#
# # And we define a simple grammar to extract it.
# parser = grammar(
#     {
#         "Doc": seq("commentStart", "comment*"),
#         "Comment": seq("comment+"),
#         "Code": seq("_+"),
#     }
# )
#
# with open(Path(__file__).parent.parent / "src/py/coda/domish.py", "rt") as f:
#     for atom in marks(python, f.read()):
#         print(atom)

# EOF
