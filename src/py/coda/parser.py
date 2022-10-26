from .reparser import Marks, Marker, marks
from .domish import node, toXML
from typing import NamedTuple, Optional
from enum import Enum


class Cardinality(Enum):
    Optional = 0
    One = 1
    Many = 2
    OneOrMore = 3


C = Cardinality


class Step(NamedTuple):
    accepts: Optional[list[str]] = None
    rejects: Optional[list[str]] = None
    cardinality: Cardinality = Cardinality.One


def matchStep(step: Step, marker: Marker) -> bool:
    """Matches the given marker with the marker pattern"""
    if step.rejects and marker.type in step.rejects:
        return False
    else:
        return (not step.accepts) or marker.type in step.accepts


def matchSteps(
    steps: list[Step], markers: list[Marker], start: int = 0
) -> Optional[list[int]]:
    """Given a list of marker patterns, tries to match the patterns in sequence
    so that they match the given markers."""
    matched: list[int] = [0 for _ in steps]
    i: int = start
    j: int = 0
    n: int = len(markers)
    m: int = len(steps)
    has_matched: bool = True
    # We start from the last marker and the last step. We'll exit
    # if we've matched all the steps,
    while i < n and j < m and has_matched:
        # Wish we had i-- there
        marker = markers[i]
        i += 1
        has_matched = False
        while j < m:
            step = steps[j]
            if matchStep(step, marker):
                if matched[j] > 0 and step.cardinality.value <= Cardinality.One.value:
                    # We have already reached our limit of matches, so we need
                    # to consider this one as a fail.
                    j += 1
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
                    j += 1
    return matched


python = Marks(
    {
        "commentStart": r"#\s*\-\-\s*\n",
        "comment": r"#(?P<text>[^\n]*)\n",
    },
    {},
)


rules = {
    "comment": [Step(["commentStart"], None, C.One), Step(["comment"], None, C.Many)],
    "code": [Step(None, ["commentStart"], C.Many)],
}

with open("src/py/coda/domish.py", "rt") as f:
    markers = marks(python, f.read())
    n = len(markers)
    i = 0
    doc = node("document")
    while i < n:
        j = i
        for rule, steps in rules.items():
            if matched := matchSteps(steps, markers, i):
                count = sum(matched)
                j = i + count
                value = "".join(_.text for _ in markers[i:j])
                doc.children.append(node(rule, {"value": value}))
                break
        if j == i:
            i += 1
        else:
            i = j

print(toXML(doc))

# EOF
