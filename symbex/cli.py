import click
import pathlib

from .lib import code_for_node, find_symbol_nodes


@click.command()
@click.version_option()
@click.argument("symbols", nargs=-1)
@click.option(
    "files", "-f", "--file", type=click.File("r"), multiple=True, help="Files to search"
)
@click.option(
    "directories",
    "-d",
    "--directory",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    multiple=True,
    help="Directories to search",
)
def cli(symbols, files, directories):
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
        # Search a specific file
        symbex MyClass -f my_file.py
    \b
        # Search within a specific directory and its subdirectories
        symbex Database -d ~/projects/datasette

    """
    if not files and not directories:
        directories = ["."]
    files = list(files)
    for directory in directories:
        files.extend(pathlib.Path(directory).rglob("*.py"))
    pwd = pathlib.Path(".").resolve()
    for file in files:
        code = file.read_text("utf-8") if hasattr(file, "read_text") else file.read()
        nodes = find_symbol_nodes(code, symbols)
        for node in nodes:
            # If file is within pwd, print relative path
            # else print absolute path
            if pwd in file.resolve().parents:
                path = file.resolve().relative_to(pwd)
            else:
                path = file.resolve()
            snippet, line_no = code_for_node(code, node)
            print("# File:", path, "Line:", line_no)
            print(snippet)
            print()
