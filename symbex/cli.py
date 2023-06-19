import click
import pathlib

from .lib import code_for_node, find_symbol_nodes, read_file


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
    "--silent",
    is_flag=True,
    help="Silently ignore Python files with parse errors",
)
def cli(symbols, files, directories, signatures, silent):
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
    """
    if not symbols and not signatures:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()
    if signatures and not symbols:
        symbols = ["*"]
    if not files and not directories:
        directories = ["."]

    def iterate_files():
        yield from (pathlib.Path(f) for f in files)
        for directory in directories:
            for path in pathlib.Path(directory).rglob("*.py"):
                if path.is_file():
                    yield path

    pwd = pathlib.Path(".").resolve()
    for file in iterate_files():
        code = read_file(file)
        try:
            nodes = find_symbol_nodes(code, str(file), symbols)
        except SyntaxError as ex:
            if not silent:
                click.secho(f"# Syntax error in {file}: {ex}", err=True, fg="yellow")
            continue
        for node, class_name in nodes:
            # If file is within pwd, print relative path
            # else print absolute path
            if pwd in file.resolve().parents:
                path = file.resolve().relative_to(pwd)
            else:
                path = file.resolve()
            snippet, line_no = code_for_node(code, node, class_name, signatures)
            bits = ["# File:", path]
            if class_name:
                bits.extend(["Class:", class_name])
            bits.extend(["Line:", line_no])
            print(*bits)
            print(snippet)
            print()
