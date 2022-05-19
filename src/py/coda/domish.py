from typing import NamedTuple, Optional, Union, Iterator, Callable

TAttributes = dict[str, Union[str, int, float, bool]]

# --
# # DOMish
#
# A minimal implementation of a DOM-like serializable data structure
class Node(NamedTuple):
    name: str
    attributes: TAttributes
    children: list["Node"]


def toXML(node: Node) -> str:
    return "".join(iterXML(node))


def iterXML(node: Node) -> Iterator[str]:
    value: str = (
        f"{node.attributes['value']}"
        if node.attributes and "value" in node.attributes
        else ""
    ).replace(">", "&gt;")
    if node.name == "#text":
        yield value
    elif node.name == "#comment":
        yield "<!--"
        yield value
        yield "-->"
    elif node.name == "#cdata":
        yield "<![CDATA["
        yield value
    elif node.name == "#doctype":
        yield f"<!DOCTYPE {value}>"
    else:
        yield f"<{node.name}"
        for k, v in (node.attributes or {}).items():
            w = v.replace("&", "&amp;").replace('"', "&quot;").replace("\n", " ")
            yield f' {k}="{w}"'
        if not node.children:
            yield " />"
        else:
            yield ">"
            for _ in node.children:
                yield from iterXML(_)
            yield f"</{node.name}>"


def node(name: str, attributes: Optional[dict] = None, *children: Node) -> Node:
    return Node(name, attributes or {}, [_ for _ in children] if children else [])


class Factory:
    def __getattr__(self, name: str) -> Callable[[Optional[TAttributes], Node], Node]:
        def wrapper(attributes: Optional[TAttributes] = None, *children: Node) -> Node:
            return node(name, attributes, *children)

        return wrapper


html = Factory()

# EOF
