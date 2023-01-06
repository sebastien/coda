from .reparser import Marks, marks
from .statemachine import StateMachine, Transition, Status, TMachine, TAtom, iterPretty
from pathlib import Path
from typing import Optional

# --
# The next step after our `statemachine` notebook is to integrate the
# statemachines so that we can express grammars in a more natural way,
# and derive the state machine from the grammar.
#
# References:
# - https://swtch.com/~rsc/regexp/regexp1.html
# - https://piumarta.com/software/peg/
# - https://bford.info/pub/lang/peg/


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
        # --
        # First step, we extract the cardinality
        if (card := match[-1]) in "?+*":
            name = match[:-1]
        else:
            name = match
            card = ""
        name = "*" if name == "_" else name
        # --
        # We get the state machine, and its transitions. The
        # --
        # Now, based on the cardinality we add specific transitions
        match card:
            case "":
                # --
                # If it's a single match, so when we match this step, we go
                res[j] = {name: Transition(0, Status.Complete)}
                j += 1
            case "?":
                res[j] = {
                    name: Transition(0, Status.Complete),
                    "*": Transition(0, Status.End),
                }
                j += 1
            case "+":
                # We start with a transition that matches the `name`
                res[j] = {
                    name: Transition(j + 1, Status.Partial),
                }
                # Then the next step can match `name` again, or end then.
                res[j + 1] = {
                    name: Transition(j + 1, Status.Partial),
                    "*": Transition(0, Status.End),
                }
                j += 2
            case "*":
                # We start with a transition that matches the `name`
                res[j] = {
                    name: Transition(j + 1, Status.Partial),
                    "*": Transition(0, Status.End),
                }
                # Then the next step can match `name` again, or end then.
                res[j + 1] = {
                    name: Transition(j + 1, Status.Partial),
                    "*": Transition(0, Status.End),
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
                k: Transition(remapped[_.target], _.status, _.effect, _.event)
                for k, _ in t.items()
            }
        )
        for s, t in m.items()
    }


# --
# Leaving this form here, as it's an elegant simple version, and the lack
# of reduce in Python makes it harder to scale nicely to this elegant format.
# ```
# def sor(sa: TMachine, sb: TMachine) -> TMachine:
#     """Combines the two machines so that `sa` matches OR `sb` matches."""
#     return remap(sa) | remap(sa, len(sa)) | {0: sb[0] | sa[0]}
# ```


def combine(*machines: TMachine) -> TMachine:
    """Combines the given machines into one"""
    count: int = 1
    remapped: list[TMachine] = []
    for machine in machines:
        remapped.append(remap(machine, count))
        count += len(machine)
    res: TMachine = {}
    start: dict[TAtom, Transition] = {}
    for machine in remapped:
        res |= machine
        start |= machine[0]
    return res | {0: start}


def makes(machine: TMachine, event: str) -> TMachine:
    """Returns a derivation of `machine` with any *End* transition triggering
    the `event`."""
    return {
        state: {
            atom: Transition(t.target, t.status, t.effect, event)
            if t.status in (Status.Partial, Status.Complete, Status.End)
            else t
            for atom, t in transitions.items()
        }
        for state, transitions in machine.items()
    }
    return machine


def rules(rules: dict[str, list[str]]) -> TMachine:
    """Combines all the rules in the given machines to produce the event
    denoted by the key upon succes."""

    return combine(
        *(
            makes(machine, event)
            for event, machine in {
                k: seq(*(v if isinstance(v, list) else v.split(" ")))
                for k, v in rules.items()
            }.items()
        )
    )


def grammar(definition: dict[str, TMachine]) -> TMachine:
    return StateMachine(rules(definition))


# EOF
