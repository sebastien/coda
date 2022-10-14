from code.reparser import Mark


class Combinator:
    def match(self, mark: Mark) -> bool:
        pass


class Composite(Combinator):
    def __init__(self, *items: Union[Mark, Combinator]):
        super().__init__()
        self.items: list[Combinator] = [One(_) if isinstance(_, Mark) else _]
        self.state: int = 0


class One(Combinator):
    def match(self, mark: Mark) -> bool:
        return self.mark.type == mark.type


class Sequence(Composite):
    def match(self, mark: Mark) -> bool:
        if self.state >= len(self.items):
            self.state = 0
            return False
        elif self.items[self.state].match(mark):
            pass


@dataclass
class Repeat(Combinator):
    items: list[Combinator]


@dataclass
class Any(Combinator):
    items: list[Combinator]


state = seq("block", repeat("comment"))
