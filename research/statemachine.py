from typing import Optional, Union, Callable, Iterable, Iterator
from enum import Enum
from dataclasses import dataclass

# --
# A general way to implement state machines, with the idea of using
# them for parsing.

TAtom = Union[str]
TState = Union[int]


class Status(Enum):
    Ready = 0
    # What's he start state for?
    Start = 1
    Incomplete = 2
    # A complete status means we can produce an output, but could
    # also add to it.
    Complete = 3
    # Once end reaches, the only transition out is back to start
    End = 4
    Fail = 5


@dataclass
class Transition:
    target: TState
    status: Optional[Status] = None
    effect: Optional[Callable[[TAtom, TState, TState], None]] = None
    # The transition could accumulate state
    # state: Optional[Callable[[TAtom, TState, TState], None]] = None


StateMachineEvent = Union["CompletionEvent"]


@dataclass
class CompletionEvent:
    machine: "StateMachine"
    start: int
    end: int


class StateMachine:
    def __init__(
        self,
        transitions: dict[TState, dict[TAtom, Transition]],
        *,
        name: Optional[str] = None,
    ):
        self.transitions: dict[TState, dict[TAtom, Transition]] = transitions
        self.state: TState = 0
        self.start: Optional[int] = None
        self.offset: int = 0
        self.status: Status = Status.Ready
        self.name: Optional[str] = name

    def reset(self, offset: int = 0):
        self.state = 0
        self.start = None
        self.offset = offset
        self.status = Status.Start

    def process(self, atoms: TAtom) -> Iterator[StateMachineEvent]:
        for atom in atoms:
            for event in self.feed(atom):
                yield event

    def feed(self, atom: TAtom, increment: bool = True) -> Iterator[StateMachineEvent]:
        t = self.match(atom)
        if t:
            previous = self.state
            if t.status is Status.Start:
                self.start = self.offset
            self.state = t.target
            if t.status is Status.End:
                # In case we complete a match, we fire a completion
                # event and then try to match again.
                if self.start is None:
                    raise RuntimeError(f"Transition completed with no start: {t}")
                else:
                    yield CompletionEvent(self, self.start, self.offset)
                if previous != self.state:
                    yield from self.feed(atom, False)
        else:
            if self.status is Status.Complete:
                if self.start is None:
                    raise RuntimeError(f"Transition completed with no start: {t}")
                else:
                    yield CompletionEvent(self, self.start, self.offset)
            self.start = None
            self.state = 0
        if increment:
            self.offset += 1

    def match(self, atom: TAtom) -> Optional[Transition]:
        t = self.transitions[self.state]
        if atom in t:
            return t[atom]
        elif "*" in t:
            return t["*"]
        else:
            # That's the end
            return None

    def __repr__(self):
        return f"StateMachine(name={self.name},status={self.status},start={self.start},offset={self.offset})"


def mux_all(
    stream: Iterable[TAtom], machines: list[StateMachine]
) -> Iterator[StateMachineEvent]:
    """A simple combinator to iterate over streams"""
    for atom in stream:
        for machine in machines:
            yield from machine.feed(atom)


# def seq( *atoms ):
#     for i,atom in enumerate(atoms):
#         yield i, atom


# --
# We define a state machine to recognise blocks based on a stream of tokens.
blocks = StateMachine(
    {
        0: {
            "block": Transition(1, Status.Start),
        },
        1: {"comment": Transition(2, Status.Complete)},
        # TODO: we need to indicate the end state
        2: {"comment": Transition(2, Status.Complete), "*": Transition(0, Status.End)},
    },
    name="Block",
)

# --
# We define a state machine to recognise comments, based on a stream of tokens.
comments = StateMachine(
    {
        0: {
            "comment": Transition(1, Status.Start),
        },
        1: {
            "comment": Transition(1, Status.Complete),
            "*": Transition(0, Status.End),
        },
    },
    name="Comment",
)


if __name__ == "__main__":
    print("=== TEST Parsing a stream of tokens with state machine")
    stream = ["block", "comment", "comment", "block", "comment", "line", "line"]
    expected = ["Block", "Comment", "Block", "Comment"]
    for i, match in enumerate(mux_all(stream, [blocks, comments])):
        print(f"--- match={match.machine.name} expected={expected[i]}")
        assert expected[i] == match.machine.name
    print("EOK")
# EOF
