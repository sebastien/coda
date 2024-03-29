from typing import Optional, Union, Callable, Iterable, Iterator
from enum import Enum
from dataclasses import dataclass

# --
# A general way to implement state machines, with the idea of using
# them for parsing.

TAtom = Union[str]
TState = Union[int]
TMachine = dict[TState, dict[TAtom, "Transition"]]


class Status(Enum):
    Start = 0  # The machine is in start position
    Ready = 1  # The machine is ready, but hasn't matched anything yet
    Incomplete = 2  #  Cannot form a match yet
    Partial = 3  # Matches form a partial unit
    Complete = 4  # Matches form a complete unit
    # Once end reaches, the only transition out is back to start
    End = 5
    Fail = 6


@dataclass
class Transition:
    target: TState
    status: Status
    effect: Optional[Callable[[TAtom, TState, TState], None]] = None
    event: Optional[str] = None
    # The transition could accumulate state
    # state: Optional[Callable[[TAtom, TState, TState], None]] = None


StateMachineEvent = Union["CompletionEvent"]


@dataclass
class CompletionEvent:
    machine: "StateMachine"
    name: Optional[str]
    # The `start` and `end` position in the input stream
    start: int
    end: int


# TODO: The StateMachine should be generic, and have T being the Atom type
class StateMachine:
    def __init__(
        self,
        transitions: dict[TState, dict[TAtom, Transition]],
        *,
        name: Optional[str] = None,
    ):
        self.transitions: dict[TState, dict[TAtom, Transition]] = transitions
        self.state: TState = 0
        # Start and offset are positions in the input stream
        self.start: Optional[int] = None
        self.offset: int = 0
        self.status: Status = Status.Start
        self.name: Optional[str] = name
        self.transition: Optional[Transition] = None

    def reset(self, offset: int = 0):
        self.state = 0
        self.start = None
        self.offset = offset
        self.status = Status.Start

    def process(self, atoms: Iterable[TAtom]) -> Iterator[StateMachineEvent]:
        """Processes the stream"""
        for atom in atoms:
            for event in self.feed(atom):
                yield event
        if end := self.peek():
            yield end

    def peek(self) -> Optional[StateMachineEvent]:
        """Peeks into the state machine, returning a state machine event
        if one can be created out of the current state."""
        if (
            self.start is not None
            and (status := self.status.value) >= Status.Partial.value
            and status < Status.Fail.value
        ):
            return CompletionEvent(
                self,
                self.transition.event if self.transition else None,
                self.start,
                self.offset,
            )
        else:
            return None

    def feed(self, atom: TAtom, increment: bool = True) -> Iterator[StateMachineEvent]:
        t = self.match(atom)
        self.transition = t
        if t:
            previous = self.state
            if t.status.value > Status.Ready.value and self.start is None:
                self.start = self.offset
            self.state = t.target
            self.status = t.status
            if t.status is Status.End:
                # In case we complete a match, we fire a completion
                # event and then try to match again.
                if self.start is None:
                    raise RuntimeError(f"Transition completed with no start: {t}")
                else:
                    yield CompletionEvent(self, t.event, self.start, self.offset)
                self.start = None
                if previous != self.state:
                    yield from self.feed(atom, False)
        else:
            # If there is no match and the status is complete, we yield a
            # completion event.
            if self.status is Status.Complete:
                # FIXME: We should maybe find a name to put instead of None
                yield CompletionEvent(
                    self,
                    None,
                    self.offset if self.start is None else self.start,
                    self.offset,
                )
            # TODO: Should we set start to None here?
        if increment:
            self.offset += 1

    def end(self) -> Optional[CompletionEvent]:
        return (
            CompletionEvent(
                self,
                self.transition.event if self.transition else None,
                self.offset if self.start is None else self.start,
                self.offset,
            )
            if self.status is Status.Partial
            else None
        )

    def match(self, atom: TAtom) -> Optional[Transition]:
        """Returns the first transition in the current state that matches
        the given atom."""
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


def pretty(machine: TMachine) -> str:
    return "\n".join(iterPretty(machine))


def iterPretty(machine: TMachine) -> Iterable[str]:
    for state in machine:
        yield f"{state:d}:"
        for token, transition in machine[state].items():
            event = f" #{transition.event}" if transition.event else ""
            yield f"   → {transition.target}:{token} [{str(transition.status).rsplit('.')[-1].lower()}]{event}"


def mux(
    stream: Iterable[TAtom], machines: list[StateMachine]
) -> Iterator[StateMachineEvent]:
    """Multiplexes an input stream over a set of state machines, yielding
    the result for each machine."""
    for atom in stream:
        for machine in machines:
            yield from machine.feed(atom)


if __name__ == "__main__":
    # --
    # We define a state machine to recognise blocks based on a stream of tokens.
    blocks = StateMachine(
        {
            0: {
                "block": Transition(1, Status.Incomplete),
            },
            1: {"comment": Transition(2, Status.Complete)},
            # TODO: we need to indicate the end state
            2: {
                "comment": Transition(2, Status.Complete),
                "*": Transition(0, Status.End),
            },
        },
        name="Block",
    )

    # --
    # We define a state machine to recognise comments, based on a stream of tokens.
    comments = StateMachine(
        {
            0: {
                "comment": Transition(1, Status.Incomplete),
            },
            1: {
                "comment": Transition(1, Status.Complete),
                "*": Transition(0, Status.End),
            },
        },
        name="Comment",
    )

    # --
    # Next level, we define a machine that recongnises continuous sequences.
    # For instance, we can take one that recognises `A+` and another that recognises
    # `B+`.
    aabb = StateMachine(
        {
            0: {
                "A": Transition(10, Status.Incomplete),
                "B": Transition(20, Status.Incomplete),
                "*": Transition(0, Status.Ready),
            },
            10: {
                "A": Transition(10, Status.Complete),
                "*": Transition(0, Status.End),
            },
            20: {
                "B": Transition(20, Status.Complete),
                "*": Transition(0, Status.End),
            },
        },
        name="AABB",
    )
    print("=== TEST Parsing a stream of tokens with state machine")
    stream = ["block", "comment", "comment", "block", "comment", "line", "line"]
    output = ["Block", "Comment", "Block", "Comment"]
    for i, match in enumerate(mux(stream, [blocks, comments])):
        actual = match.machine.name
        expected = output[i]
        print(
            f"... {i:02d} OK  {actual}"
            if actual == expected
            else f"... {i:02d} ERR {actual} != {expected}"
        )
        assert expected == actual
    print("--- OK")

    print("=== TEST aabb: Using a machine to match multiple sequences")
    stream = "AA AAAA BB BBBB CCCC AA BBBBB".split()
    output = [_ for _ in stream if _[0] in "AB"]
    for i, match in enumerate(aabb.process(text := " ".join(stream))):
        actual = text[match.start : match.end]
        expected = output[i]
        print(
            f"... {i:02d} OK  {match.start:02d}:{match.end:02d}='{text[match.start : match.end]}'"
            if actual == expected
            else f"... {i:02d} ERR {match.start:02d}:{match.end:02d}='{text[match.start : match.end]}' != '{expected}'"
        )
        assert expected == actual
    print("--- OK")
    print("EOK")
# EOF
