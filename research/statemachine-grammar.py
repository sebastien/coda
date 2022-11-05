from coda.reparser import Marks, marks
from pathlib import Path
from statemachine import StateMachine, Transition, Status, TMachine
from typing import Optional

# --
# The next step after our `statemachine` notebook is to integrate the
# statemachines so that we can express grammars in a more natural way,
# and derive the state machine from the grammar.

# References:
# - https://swtch.com/~rsc/regexp/regexp1.html
# - https://piumarta.com/software/peg/


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
                    name: Transition(0, Status.End)
                    if is_last
                    else Transition(j + 1, Status.Partial)
                }
                j += 1
            case "?":
                res[j] = {
                    name: Transition(0, Status.End)
                    if is_last
                    else Transition(j + 1, Status.Partial),
                    "*": Transition(0, Status.End)
                    if is_last
                    else Transition(j + 1, Status.Partial),
                }
                j += 1
            case "+":
                # We start with a transition that matches the `name`
                res[j] = {
                    name: Transition(j + 1, Status.Partial),
                }
                # Then the next step can match `name` again, or end then.
                res[j + 1] = {
                    name: Transition(0, Status.End)
                    if is_last
                    else Transition(j + 1, Status.Partial),
                    "*": Transition(0, Status.End)
                    if is_last
                    else Transition(j + 1, Status.Partial),
                }
                j += 2
            case "*":
                # We start with a transition that matches the `name`
                res[j] = {
                    name: Transition(j + 1, Status.Partial),
                    "*": Transition(0, Status.End)
                    if is_last
                    else Transition(j + 1, Status.Partial),
                }
                # Then the next step can match `name` again, or end then.
                res[j + 1] = {
                    name: Transition(j, Status.End)
                    if is_last
                    else Transition(j + 1, Status.Partial),
                    "*": Transition(0, Status.End)
                    if is_last
                    else Transition(j + 1, Status.Partial),
                }
                j += 2
        i += 1
    return res


def remap(m: TMachine, offset: int = 10) -> TMachine:
    """Remaps the machine states so that all the states and numbers are in
    incremental order from offset, except the initial state of 0"""

    states: set[int] = set()
    for state, transitions in m.items():
        states.add(state)
        states = states | {_.target for _ in transitions.values()}
    remapped: dict[int, int] = {
        k: offset + i if k != 0 else k for i, k in enumerate(sorted(states))
    }
    return {
        remapped[s]: (
            {
                k: Transition(remapped[_.target], _.status, _.effect)
                for k, _ in t.items()
            }
        )
        for s, t in m.items()
    }


def sor(sa: TMachine, sb: TMachine) -> TMachine:
    """Combines the two machines so that `sa` matches OR `sb` matches."""
    return remap(sa) | remap(sa, len(sa)) | {0: sb[0] | sa[0]}


if __name__ == "__main__":
    print("=== TEST seq: defining a sequence of transitions")
    res = seq("commentStart", "commentLine+")
    # NOTE: remap and sor should be equivalent
    # res = remap(res)
    # res = sor(res, res)
    print(remap(res))
    machine = StateMachine(res, name="Comments")
    stream = [
        "commentStart",
        "commentLine",
        "commentLine",
        "code",
        "commentStart",
        "commentLine",
    ]
    expected = [
        ("Comment", 0, 3),
        ("Comment", 4, 5),
    ]
    for atom in stream:
        print(f"--- IN  {atom}")
        for match in machine.feed(atom):
            print(f"... OUT {stream[match.start:match.end+1]}")
    if m := machine.peek():
        print(f"... OUT {stream[m.start:m.end+1]}")
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
