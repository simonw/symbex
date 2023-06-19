import fnmatch
import ast
from ast import literal_eval, parse, AST, AsyncFunctionDef, FunctionDef, ClassDef
import codecs
from itertools import zip_longest
import re
from typing import Iterable, List, Optional, Tuple


def find_symbol_nodes(
    code: str, filename: str, symbols: Iterable[str]
) -> List[Tuple[AST, Optional[str]]]:
    "Returns ast Nodes matching symbols"
    # list of (AST, None-or-class-name)
    matches = []
    module = parse(code)
    for node in module.body:
        if not isinstance(node, (ClassDef, FunctionDef, AsyncFunctionDef)):
            continue
        name = getattr(node, "name", None)
        if match(name, symbols):
            matches.append((node, None))
        # If it's a class search its methods too
        if isinstance(node, ClassDef):
            for child in node.body:
                if isinstance(child, (FunctionDef, AsyncFunctionDef)):
                    qualified_name = f"{name}.{child.name}"
                    if match(qualified_name, symbols):
                        matches.append((child, name))

    return matches


def code_for_node(
    code: str, node: AST, class_name: str, signatures: bool
) -> Tuple[str, int]:
    "Returns the code for a given node"
    lines = code.split("\n")
    start = None
    end = None
    if signatures:
        if isinstance(node, (FunctionDef, AsyncFunctionDef)):
            definition, lineno = function_definition(node), node.lineno
            if class_name:
                definition = "    " + definition
            return definition, lineno
        elif isinstance(node, ClassDef):
            return class_definition(node), node.lineno
        else:
            # Not a function or class, fall back on just the line
            start = node.lineno - 1
            end = node.lineno
    else:
        # If the node has decorator_list, include those too
        if getattr(node, "decorator_list", None):
            start = node.decorator_list[0].lineno - 1
        else:
            start = node.lineno - 1
        end = node.end_lineno
    output = "\n".join(lines[start:end])
    # If it's in a class, indent it 4 spaces
    return output, start + 1


def match(name: str, symbols: Iterable[str]) -> bool:
    "Returns True if name matches any of the symbols, resolving wildcards"
    if name is None:
        return False
    for search in symbols:
        if "*" not in search:
            # Exact matches only
            if name == search:
                return True
        elif search.count(".") == 1:
            # wildcards are supported either side of the dot
            if "." in name:
                class_match, method_match = search.split(".")
                class_name, method_name = name.split(".")
                if fnmatch.fnmatch(class_name, class_match) and fnmatch.fnmatch(
                    method_name, method_match
                ):
                    return True
        else:
            if fnmatch.fnmatch(name, search) and "." not in name:
                return True

    return False


def function_definition(function_node: AST):
    function_name = function_node.name

    all_args = [
        *function_node.args.posonlyargs,
        *function_node.args.args,
        *function_node.args.kwonlyargs,
    ]

    # For position only args like "def foo(a, /, b, c)"
    # we can look at the length of args.posonlyargs to see
    # if any are set and, if so, at what index the `/` should go
    position_of_slash = len(function_node.args.posonlyargs)

    # For func_keyword_only_args(a, *, b, c) the length of
    # the kwonlyargs tells us how many spaces back from the
    # end the star should be displayed
    position_of_star = len(all_args) - len(function_node.args.kwonlyargs)

    # function_node.args.defaults may have defaults
    # corresponding to function_node.args.args - but
    # if defaults has 2 and args has 3 then those
    # defaults correspond to the last two args
    defaults = [None] * (len(all_args) - len(function_node.args.defaults))
    for default in function_node.args.defaults:
        try:
            value = literal_eval(default)
            if isinstance(value, str):
                value = f'"{value}"'
        except ValueError:
            value = getattr(default, "id", "...")
        defaults.append(value)

    arguments = []

    for i, (arg, default) in enumerate(zip_longest(all_args, defaults)):
        if position_of_slash and i == position_of_slash:
            arguments.append("/")
        if position_of_star and i == position_of_star:
            arguments.append("*")
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {annotation_definition(arg.annotation)}"

        if default:
            arg_str = f"{arg_str}={default}"

        arguments.append(arg_str)

    if function_node.args.vararg:
        arguments.append(f"*{function_node.args.vararg.arg}")

    if function_node.args.kwarg:
        arguments.append(f"**{function_node.args.kwarg.arg}")

    arguments_str = ", ".join(arguments)

    return_annotation = ""
    if function_node.returns:
        return_annotation = f" -> {annotation_definition(function_node.returns)}"

    def_ = "def "
    if isinstance(function_node, AsyncFunctionDef):
        def_ = "async def "

    return f"{def_}{function_name}({arguments_str}){return_annotation}"


def class_definition(class_def):
    # Base classes
    base_classes = []
    for base in class_def.bases:
        if getattr(base, "id", None):
            base_classes.append(base.id)
    base_classes_str = ", ".join(base_classes)

    # Keywords (including metaclass)
    keywords = {k.arg: getattr(k.value, "id", str(k.value)) for k in class_def.keywords}
    metaclass = keywords.pop("metaclass", None)
    keyword_str = ", ".join([f"{k}=..." for k in keywords])

    if base_classes_str and keyword_str:
        signature = f"{base_classes_str}, {keyword_str}"
    elif base_classes_str:
        signature = base_classes_str
    elif keyword_str:
        signature = keyword_str
    else:
        signature = ""

    if metaclass:
        sep = ", " if signature else ""
        signature = f"{signature}{sep}metaclass={metaclass}"

    if signature:
        signature = f"({signature})"

    class_definition = f"class {class_def.name}{signature}"

    return class_definition


def annotation_definition(annotation: AST) -> str:
    if annotation is None:
        return ""
    elif isinstance(annotation, ast.Name):
        return annotation.id
    elif isinstance(annotation, ast.Subscript):
        value = annotation_definition(annotation.value)
        slice = annotation_definition(annotation.slice)
        return f"{value}[{slice}]"
    elif isinstance(annotation, ast.Index):
        return annotation_definition(annotation.value)
    elif isinstance(annotation, ast.Tuple):
        elements = ", ".join(annotation_definition(e) for e in annotation.elts)
        return f"({elements})"
    else:
        return "?"


def read_file(path):
    encoding_pattern = r"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)"
    default_encoding = "utf-8"

    with open(path, "r", encoding=default_encoding, errors="ignore") as f:
        first_512_bytes = f.read(512)
        first_two_lines = "\n".join(first_512_bytes.split("\n")[:2])

        match = re.search(encoding_pattern, first_two_lines, re.MULTILINE)
        if match:
            encoding = match.group(1)
        else:
            encoding = default_encoding

    try:
        with codecs.open(path, "r", encoding=encoding) as f:
            content = f.read()
    except LookupError:
        # If the detected encoding is not valid, try again with utf-8
        with codecs.open(path, "r", encoding=default_encoding) as f:
            content = f.read()

    return content
