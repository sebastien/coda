from coda.reparser import Marks, marks
from pathlib import Path
from statemachine import Transition

python: Marks = Marks(
    {
        "commentStart": r"#\s*\-\-\s*\n",
        "comment": r"#(?P<text>[^\n]*)\n",
    },
    {},
)


def seq(*matches: str) -> dict[int, dict[str,Transition]]:
    res:dict[int,dict[str,Transition]] = {0:{}}
    n = len(matches)
    j:int = 0
    while i < n:
        match = matches[i]
        name: str = ""
        card: str = ""
        is_last:bool = i + 1 < n
        next_name:Optional[str] = matches[i + 1] if not is_last else None
        if (card := match[-1]) in "?+*":
            name = match[:-1]
        else:
            name = match
            card = ""

        step = res[j]
        match card:
            case "":
                step[name] =Transition(0,Status.End) if is_last else Transition(j+1)
                j +=1
                res[j] = {}
            case "?":
                step[name] =Transition(0,Status.End) if is_last else Transition(j+1)
                res[j] = {
                    name:Transition(0,Status.End) if is_last else Transition(j+1),
                    "*":Transition(0,Status.End) if is_last else Transition(j+1)
                }
                j +=1
            case "+":
                res[j] = {
                    name:Transition(j+1),
                }
                j +=1
                res[j] = {
                    name:Transition(0,Status.End) if is_last else Transition(j),
                }
            case "*":

                }




def grammar(rules: dict[str, dict[str, Transition]]):
    return None


parser = grammar(
    {
        "Doc": seq("commentStart", "comment*"),
        "Comment": seq("comment+"),
        "Code": seq("_+"),
    }
)

with open(Path(__file__).parent.parent / "src/py/coda/domish.py", "rt") as f:
    for atom in marks(python, f.read()):
        print(atom)

# EOF
