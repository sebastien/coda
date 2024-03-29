from typing import Optional, Union, Callable, Iterable, Iterator, Self
from enum import Enum
from dataclasses import dataclass

# rn --
# A general way to implement state machines, with the idea of using
# them for parsing.

TAtom = str
TState = int
TMachine = dict[TState, dict[TAtom, "Transition"]]


class Status(Enum):
    Start = 0  # The machine is in start position
    Ready = 1  # The machine is ready, but hasn't matched anything yet
    Incomplete = 2  #  Cannot form a match yet
    Partial = 3  # Can form a match, but may be expanded
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
    # The `start` and `end` position in the input stream, end is exclusive.
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

    def reset(self, offset: int = 0) -> Self:
        self.state = 0
        self.start = None
        self.offset = offset
        self.status = Status.Start
        self.transition = None
        return self

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
                self.offset + (1 if status is Status.Complete.value else 0),
            )
        else:
            return None

    def run(self, atoms: Iterator[TAtom]) -> Iterator[StateMachineEvent]:
        for atom in atoms:
            yield from self.feed(atom)
        if match := self.end():
            yield match

    def feed(
        self, atom: TAtom, *, increment: bool = True, previous: Optional[int] = None
    ) -> Iterator[StateMachineEvent]:
        self.transition = t = self.match(atom)
        if t:
            # If we have a matching transition, then the go through it
            if t.status.value > Status.Ready.value and self.start is None:
                # If the machine is ready and start is None, we have a new match
                # TODO: Shouldn't we detect if the previous transition was compelte?
                self.start = self.offset
            self.state = t.target
            self.status = t.status
            if t.status is Status.End:
                # In case we reach the End of a match, we fire a completion
                # event…
                if self.start is None:
                    raise RuntimeError(f"Transition completed with no start: {t}")
                elif self.offset == self.start and self.start == previous:
                    # This is the edge case when we have a machine with
                    # `{0:{"*":(0,"End")}}` which may not consume anything.
                    # FIXME: This is a bit inelegant, and we should ensure
                    # that the conditions are representative.
                    pass
                else:
                    yield CompletionEvent(
                        self,
                        t.event,
                        self.start,
                        self.offset,
                    )
                start = self.start
                self.start = None
                # And then try to match again. This is required as an End state
                # means that the current set of transitions can't match any further,
                # and so we need to restart with the target state.
                if increment is True:
                    yield from self.feed(atom, increment=False, previous=start)
            else:
                # In any other case, we don't have anything specific to do.
                # Note that `Complete` transitions won't trigger a CompletionEvent
                # up until `end` is explicitely called, or an `End` transition happens.
                pass
        else:
            # If there is no match and the status is End, we yield a
            # completion event.
            if self.status is Status.End:
                # FIXME: We should maybe find a name to put instead of None
                yield CompletionEvent(
                    self,
                    None,
                    self.offset if self.start is None else self.start,
                    self.offset,
                )
        # In all cases, we incremenet the offset as we got fed an atom
        if increment:
            self.offset += 1

    def end(self) -> Optional[CompletionEvent]:
        if self.status is Status.Complete:
            return CompletionEvent(
                self,
                self.transition.event if self.transition else None,
                self.offset if self.start is None else self.start,
                self.offset,
            )
        else:
            return None

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

    def pretty(self) -> str:
        return pretty(self.transitions)

    def __repr__(self):
        return f"StateMachine(name={self.name},status={self.status},start={self.start},offset={self.offset},transition={self.transition})"


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


# EOF
