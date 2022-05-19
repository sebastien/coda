from .reparser import Grammar, Marker, marks
from typing import NamedTuple, Optional, Iterable
from enum import Enum


class Cardinality(Enum):
    Optional = 0
    One = 1
    Many = 2
    OneOrMore = 3


C = Cardinality

# FIXME: Rename
class Step(NamedTuple):
    markers: Optional[list[str]] = None
    cardinality: Cardinality = Cardinality.One


def matchStep(step: Step, marker: Marker) -> bool:
    """Matches the given marker with the marker pattern"""
    return step.markers is None or marker.type in step.markers


def matchSteps(
    steps: list[Step], markers: list[Marker], end: int = -1
) -> Optional[list[int]]:
    """Given a list of marker patterns, tries to match the patterns in sequence
    so that they match the given markers."""
    matched: list[int] = [0 for _ in steps]
    n: int = len(steps)
    j: int = n - 1
    i: int = end if end >= 0 else len(markers) + end
    has_matched: bool = True
    # We start from the last marker and the last step. We'll exit
    # if we've matched all the steps,
    while i >= 0 and j >= 0 and has_matched:
        # Wish we had i-- there
        marker = markers[i]
        i -= 1
        has_matched = False
        while j >= 0:
            step = steps[j]
            if matchStep(step, marker):
                if matched[j] > 0 and step.cardinality.value <= Cardinality.One.value:
                    # We have already reached our limit of matches, so we need
                    # to consider this one as a fail.
                    j -= 1
                    continue
                else:
                    # We have a match, we're all good and can get to the next
                    # marker
                    matched[j] += 1
                    has_matched = True
                    break
            else:
                if matched[j] == 0 and step.cardinality in (
                    Cardinality.One,
                    Cardinality.OneOrMore,
                ):
                    # Here we didn't have a match, and if there was no existing
                    # match, we'll need to do an early exit.
                    return None
                else:
                    # Otherwise we continue with the next rule.
                    j -= 1
    return matched


python = Grammar(
    {
        "commentStart": r"#\s*\-\-\s*\n",
        "comment": r"#(?P<text>[^\n]*)\n",
    },
    {},
)

rules = {
    "comment": [Step(["commentStart"], C.One), Step(["comment"], C.Many)],
    "code": [Step(None, C.Many)],
}

with open("src/py/coda/domish.py", "rt") as f:
    markers = marks(python, f.read())
    n = len(markers)
    i = n - 1
    while i >= 0:
        j: int = i
        for rule, steps in rules.items():
            if matched := matchSteps(steps, markers, i):
                count = sum(matched)
                print(f"MATCHED {rule} of {count} {i}→{count}/{i}")
                j = i - count
                break
        if j == i:
            break
        else:
            i = j

# EOF
