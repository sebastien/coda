# --
# # Statemachines: state management
#
# We expand on our state machine implementation to support more expressive
# grammars that can store state variables, access them and evaluate
# predicates against them. In other words, state machines would then
# have transitions that also take the current state in consideration.

nd_grammar = dict(
    # > denotes a substate: we start a parallel machine that will end
    # on an `emphasis` (item 3).
    Emphasis=["emphasis", ">", "emphasis"],
    Code=["code", ">", "code"],
    Term=["term", ">", "term"],
)

if __name__ == "__main__":
    # Wish we had recursive types in Python

    expected: dict[str, str | list[str | list[str | list[str | list[str]]]]] = {}
    # --
    # Parsing inlines in markdown is a good example of requiring
    # state:

    a = "_term*emphasis`code`*_"
    expected[a] = [["term", ["emphasis", ["code", "code"]]]]
    b = "_term *emphasis`_ code`*"
    expected[b] = [["term", "*emphasis`"], " code`*"]

# EOF
