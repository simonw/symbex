import fnmatch
from ast import parse, AST
from typing import Iterable, Tuple


def find_symbol_nodes(code: str, symbols: Iterable[str]) -> Iterable[AST]:
    "Returns ast Nodes matching symbols"
    matches = []
    module = parse(code)
    for node in module.body:
        name = getattr(node, "name", None)
        if match(name, symbols):
            matches.append(node)
    return matches


def code_for_node(code: str, node: AST) -> Tuple[str, int]:
    "Returns the code for a given node"
    lines = code.split("\n")
    # If the node has decorator_list, include those too
    if getattr(node, "decorator_list", None):
        start = node.decorator_list[0].lineno - 1
    else:
        start = node.lineno - 1
    end = node.end_lineno
    return "\n".join(lines[start:end]), start + 1


def match(name: str, symbols: Iterable[str]) -> bool:
    "Returns True if name matches any of the symbols, resolving wildcards"
    if name is None:
        return False
    for symbol in symbols:
        if "*" not in symbol:
            if name == symbol:
                return True
        else:
            if fnmatch.fnmatch(name, symbol):
                return True

    return False
