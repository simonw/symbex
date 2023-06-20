import ast
import click
import pathlib

from .lib import code_for_node, find_symbol_nodes, read_file, type_summary


@click.command()
@click.version_option()
@click.argument("symbols", nargs=-1)
@click.option(
    "files",
    "-f",
    "--file",
    type=click.Path(file_okay=True, dir_okay=False),
    multiple=True,
    help="Files to search",
)
@click.option(
    "directories",
    "-d",
    "--directory",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    multiple=True,
    help="Directories to search",
)
@click.option(
    "-s",
    "--signatures",
    is_flag=True,
    help="Show just function and class signatures",
)
@click.option(
    "--docstrings",
    is_flag=True,
    help="Show function and class signatures plus docstrings",
)
@click.option(
    "--count",
    is_flag=True,
    help="Show count of matching symbols",
)
@click.option(
    "--silent",
    is_flag=True,
    help="Silently ignore Python files with parse errors",
)
@click.option(
    "async_",
    "--async",
    is_flag=True,
    help="Filter async functions",
)
@click.option(
    "--function",
    is_flag=True,
    help="Filter functions",
)
@click.option(
    "class_",
    "--class",
    is_flag=True,
    help="Filter classes",
)
@click.option(
    "--documented",
    is_flag=True,
    help="Filter functions with docstrings",
)
@click.option(
    "--undocumented",
    is_flag=True,
    help="Filter functions without docstrings",
)
@click.option(
    "--typed",
    is_flag=True,
    help="Filter functions with type annotations",
)
@click.option(
    "--untyped",
    is_flag=True,
    help="Filter functions without type annotations",
)
@click.option(
    "--partially-typed",
    is_flag=True,
    help="Filter functions with partial type annotations",
)
@click.option(
    "--fully-typed",
    is_flag=True,
    help="Filter functions with full type annotations",
)
def cli(
    symbols,
    files,
    directories,
    signatures,
    docstrings,
    count,
    silent,
    async_,
    function,
    class_,
    documented,
    undocumented,
    typed,
    untyped,
    partially_typed,
    fully_typed,
):
    """
    Find symbols in Python code and print the code for them.

    Example usage:

    \b
        # Search current directory and subdirectories
        symbex my_function MyClass

    \b
        # Search using a wildcard
        symbex 'test_*'

    \b
        # Find a specific class method
        symbex 'MyClass.my_method'

    \b
        # Find class methods using wildcards
        symbex '*View.handle_*'

    \b
        # Search a specific file
        symbex MyClass -f my_file.py

    \b
        # Search within a specific directory and its subdirectories
        symbex Database -d ~/projects/datasette

    \b
        # View signatures for all symbols in current directory and subdirectories
        symbex -s

    \b
        # View signatures for all test functions
        symbex 'test_*' -s

    \b
        # View signatures for all async functions with type definitions
        symbex --async --typed -s

    \b
        # Count the number of --async functions in the project
        symbex --async --count
    """
    if count or docstrings:
        signatures = True
    # Show --help if no filter options are provided:
    if not any(
        [
            symbols,
            signatures,
            async_,
            function,
            class_,
            documented,
            undocumented,
            typed,
            untyped,
            partially_typed,
            fully_typed,
        ]
    ):
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()
    # Default to '*' if --signatures or filters are provided without symbols
    if (
        any(
            [
                signatures,
                async_,
                function,
                class_,
                documented,
                undocumented,
                typed,
                untyped,
                partially_typed,
                fully_typed,
            ]
        )
        and not symbols
    ):
        symbols = ["*"]
    if not files and not directories:
        directories = ["."]

    def iterate_files():
        yield from (pathlib.Path(f) for f in files)
        for directory in directories:
            for path in pathlib.Path(directory).rglob("*.py"):
                if path.is_file():
                    yield path

    # Filter symbols by type
    def filter(node: ast.AST) -> bool:
        return True

    # If any --filters were supplied, handle them:
    if any(
        [
            async_,
            function,
            class_,
            documented,
            undocumented,
            typed,
            untyped,
            partially_typed,
            fully_typed,
        ]
    ):

        def filter(node: ast.AST) -> bool:
            # Filters must ALL match
            if async_ and not isinstance(node, ast.AsyncFunctionDef):
                return False
            if function and not isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                return False
            if class_ and not isinstance(node, ast.ClassDef):
                return False
            if documented and not ast.get_docstring(node):
                return False
            if undocumented and ast.get_docstring(node):
                return False
            summary = type_summary(node)
            # if no summary, type filters all fail
            if not summary and (typed or untyped or partially_typed or fully_typed):
                return False
            # Apply type filters
            if typed and not summary.partially:
                return False
            if untyped and summary.partially:
                return False
            if partially_typed and not (summary.partially and not summary.fully):
                return False
            if fully_typed and not summary.fully:
                return False

            return True

    pwd = pathlib.Path(".").resolve()
    num_matches = 0
    for file in iterate_files():
        code = read_file(file)
        try:
            nodes = find_symbol_nodes(code, str(file), symbols)
        except SyntaxError as ex:
            if not silent:
                click.secho(f"# Syntax error in {file}: {ex}", err=True, fg="yellow")
            continue
        for node, class_name in nodes:
            if not filter(node):
                continue
            if count:
                num_matches += 1
                continue
            # If file is within pwd, print relative path
            if pwd in file.resolve().parents:
                path = file.resolve().relative_to(pwd)
            else:
                # else print absolute path
                path = file.resolve()
            snippet, line_no = code_for_node(
                code, node, class_name, signatures, docstrings
            )
            bits = ["# File:", path]
            if class_name:
                bits.extend(["Class:", class_name])
            bits.extend(["Line:", line_no])
            print(*bits)
            print(snippet)
            print()
    if count:
        click.echo(num_matches)
