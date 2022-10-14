from typing import Optional, Union, Callable, Iterator
from enum import Enum
from dataclasses import dataclass

# --
# A general way to implement state machines, with the idea of using
# them for parsing.

TAtom = Union[str]
TState = Union[int]


class Status(Enum):
    Ready = 0
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


StateMachineEvent = Union["Completion"]


@dataclass
class Completion:
    machine: "StateMachine"
    start: int
    end: int


class StateMachine:
    def __init__(self, transitions: dict[TState, dict[TAtom, Transition]]):
        self.transitions: dict[TState, dict[TAtom, Transition]] = transitions
        self.state: TState = 0
        self.start: Optional[int] = None
        self.offset: int = 0
        self.status: Status = Status.Ready

    def reset(self, offset: int = 0):
        self.state = 0
        self.start = None
        self.offset: int = offset
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
                    yield Completion(self, self.start, self.offset)
                if previous != self.state:
                    yield from self.feed(atom, False)
        else:
            if self.status is Status.Complete:
                if self.start is None:
                    raise RuntimeError(f"Transition completed with no start: {t}")
                else:
                    yield Completion(self, self.start, self.offset)
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


# def seq( *atoms ):
#     for i,atom in enumerate(atoms):
#         yield i, atom


blocks = StateMachine(
    {
        0: {
            "block": Transition(1, Status.Start),
        },
        1: {"comment": Transition(2, Status.Complete)},
        # TODO: we need to indicate the end state
        2: {"comment": Transition(2, Status.Complete), "*": Transition(0, Status.End)},
    }
)

comments = StateMachine(
    {
        0: {
            "comment": Transition(1, Status.Start),
        },
        1: {
            "comment": Transition(1, Status.Complete),
            "*": Transition(0, Status.End),
        },
    }
)


stream = ["block", "comment", "comment", "block", "comment", "line", "line"]
for match in comments.process(stream):
    print(match)
