import ast
import click
import csv
import dataclasses
import importlib
import inspect
import json
import pathlib
import site
import subprocess
import sys
from typing import TextIO, Iterable, Literal, Tuple, List, Iterator, Optional

from .lib import (
    code_for_node,
    find_symbol_nodes,
    import_line_for_function,
    read_file,
    type_summary,
)


@dataclasses.dataclass
class Symbol:
    symbol_id: str
    output_identifier_line: Optional[str]
    output_import_line: Optional[str]
    snippet: str
    filepath: Optional[pathlib.Path] = None
    line_no: Optional[int] = None


def is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def to_output(
    fp: TextIO,
    lines: Iterable[Tuple[str, str]],
    format: Literal["csv", "tsv", "json", "nl"] = "csv",
) -> None:
    if format == "nl":
        for id, content in lines:
            line = json.dumps({"id": id, "code": content})
            fp.write(line + "\n")
        return

    elif format == "json":
        fp.write("[")
        first = True
        for id, content in lines:
            line = json.dumps({"id": id, "code": content})
            if first:
                fp.write(line)
                first = False
            else:
                fp.write(",\n " + line)
        fp.write("]\n")
        return

    dialect = "excel" if format == "csv" else "excel-tab"
    writer = csv.writer(fp, dialect=dialect)
    writer.writerow(["id", "code"])
    for id, content in lines:
        writer.writerow([id, content])


def search(
    symbols: Optional[List[str]] = None,
    files: Optional[List[pathlib.Path]] = None,
    directories: Optional[List[pathlib.Path]] = None,
    stdlib: bool = False,
    excludes: Optional[List[pathlib.Path]] = None,
    signatures: bool = False,
    no_file: bool = False,
    imports: bool = False,
    modules: Optional[List[str]] = None,
    sys_paths: Optional[List[str]] = None,
    docs: bool = False,
    silent: bool = False,
    function: bool = False,
    async_: bool = False,
    unasync: bool = False,
    class_: bool = False,
    documented: bool = False,
    undocumented: bool = False,
    public: bool = False,
    private: bool = False,
    dunder: bool = False,
    typed: bool = False,
    untyped: bool = False,
    partially_typed: bool = False,
    fully_typed: bool = False,
    no_init: bool = False,
) -> Iterator[Symbol]:
    # Initialize defaults for list-type options.
    if symbols is None:
        symbols = []
    if files is None:
        files = []
    if directories is None:
        directories = []
    if excludes is None:
        excludes = []
    if sys_paths is None:
        sys_paths = []

    # Set no_init flag to imply fully_typed, per original logic.
    if no_init:
        fully_typed = True

    # If the stdlib flag is passed add the standard library folder.
    if stdlib:
        stdlib_folder = pathlib.Path(pathlib.__file__).parent.resolve()
        directories.append(stdlib_folder)
        if str(stdlib_folder) not in sys_paths:
            sys_paths.insert(0, str(stdlib_folder))
        if not directories and not files:
            silent = True

    # Default to the current directory if no files/directories were specified.
    if not files and not directories:
        directories.append(pathlib.Path("."))

    # When filters are provided but no symbols, default to searching for all symbols.
    if (
        signatures
        or async_
        or unasync
        or function
        or class_
        or documented
        or undocumented
        or public
        or private
        or dunder
        or typed
        or untyped
        or partially_typed
        or fully_typed
        or no_init
    ) and not symbols:
        symbols = ["*"]

    pwd = pathlib.Path(".").resolve()

    # Iterate over all Python files specified either individually or by searching directories.
    def iterate_files() -> Iterator[pathlib.Path]:
        for f in files:
            yield f if isinstance(f, pathlib.Path) else pathlib.Path(f)
        for directory in directories:
            for path in pathlib.Path(directory).rglob("*.py"):
                try:
                    resolved_path = path.resolve()
                except Exception:
                    continue
                if any(resolved_path.is_relative_to(ex) for ex in excludes):
                    continue
                if path.is_file():
                    yield path

    def filter_node(node: ast.AST) -> bool:
        if async_ and not isinstance(node, ast.AsyncFunctionDef):
            return False
        if function and not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False
        if unasync and not isinstance(node, ast.FunctionDef):
            return False
        if class_ and not isinstance(node, ast.ClassDef):
            return False
        if documented and not ast.get_docstring(node):
            return False
        if undocumented and ast.get_docstring(node):
            return False
        if public and node.name.startswith("_") and not is_dunder(node.name):
            return False
        if private and (is_dunder(node.name) or not node.name.startswith("_")):
            return False
        if dunder and not is_dunder(node.name):
            return False
        summary = type_summary(node)
        if not summary and (
            typed or untyped or partially_typed or fully_typed or no_init
        ):
            return False
        if typed and not summary.partially:
            return False
        if untyped and summary.partially:
            return False
        if partially_typed and not (summary.partially and not summary.fully):
            return False
        if no_init and node.name == "__init__":
            return False
        if fully_typed and not summary.fully:
            return False
        return True

    # For each file, read the code, parse it, and then for each matching symbol...
    for file in iterate_files():
        try:
            code = read_file(file)
        except UnicodeDecodeError as ex:
            if not silent:
                click.secho(f"# Unicode error in {file}: {ex}", err=True, fg="yellow")
            continue
        try:
            nodes = find_symbol_nodes(code, str(file), symbols)
        except SyntaxError as ex:
            if not silent:
                click.secho(f"# Syntax error in {file}: {ex}", err=True, fg="yellow")
            continue
        for node, class_name in nodes:
            if not filter_node(node):
                continue
            snippet, line_no = code_for_node(code, node, class_name, signatures, docs)
            try:
                resolved = file.resolve()
            except Exception:
                resolved = file
            if pwd in resolved.parents:
                rel_path = resolved.relative_to(pwd)
            else:
                rel_path = resolved
            output_identifier_line = None
            output_import_line = None
            symbol_id = None
            if not no_file:
                bits = ["# File:", str(rel_path)]
                if class_name:
                    bits.extend(["Class:", class_name])
                bits.extend(["Line:", str(line_no)])
                symbol_id = f"{rel_path}:{line_no}"
                output_identifier_line = " ".join(bits)
            if imports:
                imp_line = import_line_for_function(
                    node.name, rel_path, sys_paths or directories
                )
                if class_name:
                    # For a class, output a modified import statement.
                    imp_line = imp_line.split(" import ")[0] + " import " + class_name
                symbol_id = imp_line
                output_import_line = "# " + imp_line

            yield Symbol(
                symbol_id=symbol_id,
                output_identifier_line=output_identifier_line,
                output_import_line=output_import_line,
                snippet=snippet,
                filepath=resolved,
                line_no=line_no,
            )


#
# The cli() function just sets up extra (CSV/replace etc) behavior
#
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
@click.option("--stdlib", is_flag=True, help="Search the Python standard library")
@click.option(
    "excludes",
    "-x",
    "--exclude",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    multiple=True,
    help="Directories to exclude",
)
@click.option(
    "-s",
    "--signatures",
    is_flag=True,
    help="Show just function and class signatures",
)
@click.option(
    "-n",
    "--no-file",
    is_flag=True,
    help="Don't include the # File: comments in the output",
)
@click.option(
    "-i",
    "--imports",
    is_flag=True,
    help="Show 'from x import y' lines for imported symbols",
)
@click.option(
    "modules", "-m", "--module", multiple=True, help="Modules to search within"
)
@click.option(
    "sys_paths",
    "--sys-path",
    multiple=True,
    help="Calculate imports relative to these on sys.path",
)
@click.option(
    "--docs",
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
    "--function",
    is_flag=True,
    help="Filter functions",
)
@click.option(
    "async_",
    "--async",
    is_flag=True,
    help="Filter async functions",
)
@click.option(
    "unasync",
    "--unasync",
    is_flag=True,
    help="Filter non-async functions",
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
    "--public",
    is_flag=True,
    help="Filter for symbols without a _ prefix",
)
@click.option(
    "--private",
    is_flag=True,
    help="Filter for symbols with a _ prefix",
)
@click.option(
    "--dunder",
    is_flag=True,
    help="Filter for symbols matching __*__",
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
@click.option(
    "--no-init",
    is_flag=True,
    help="Filter to exclude any __init__ methods",
)
@click.option(
    "--check", is_flag=True, help="Exit with non-zero code if any matches found"
)
@click.option(
    "--replace",
    is_flag=True,
    help="Replace matching symbol with text from stdin",
)
@click.option("--rexec", help="Replace with the result of piping to this tool")
# Output options:
@click.option("csv_", "--csv", is_flag=True, help="Output as CSV")
@click.option("--tsv", is_flag=True, help="Output as TSV")
@click.option("json_", "--json", is_flag=True, help="Output as JSON")
@click.option("--nl", is_flag=True, help="Output as newline-delimited JSON")
@click.option("--id-prefix", help="Prefix to use for symbol IDs")
def cli(
    symbols,
    files,
    directories,
    stdlib,
    excludes,
    signatures,
    no_file,
    imports,
    modules,
    sys_paths,
    docs,
    count,
    silent,
    function,
    async_,
    unasync,
    class_,
    documented,
    undocumented,
    public,
    private,
    dunder,
    typed,
    untyped,
    partially_typed,
    fully_typed,
    no_init,
    check,
    replace,
    rexec,
    csv_,
    tsv,
    json_,
    nl,
    id_prefix,
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

    \b
        # Replace my_function with a new implementation:
        echo "def my_function(a, b):
            # This is a replacement implementation
            return a + b + 3
        " | symbex my_function --replace

    \b
        # Replace my_function with the output of a command:
        symbex first_function --rexec "sed 's/^/# /'"
        # This uses sed to comment out the function body
    """
    # Only one of --json, --csv, --tsv, --nl
    output_formats = [csv_, tsv, json_, nl]
    if sum(output_formats) > 1:
        raise click.ClickException("Only one of --csv, --tsv, --json, --nl can be used")
    if id_prefix and not sum(output_formats):
        raise click.ClickException(
            "--id-prefix can only be used with --csv, --tsv, --json or --nl"
        )
    if id_prefix is None:
        id_prefix = ""

    # Process --module options: find the module file/dir and add to our search paths.
    if modules:
        module_dirs = []
        module_files = []
        for module in modules:
            try:
                mod = importlib.import_module(module)
                mod_path = pathlib.Path(inspect.getfile(mod))
                if mod_path.stem == "__init__":
                    module_dirs.append(mod_path.parent)
                else:
                    module_files.append(mod_path)
            except ModuleNotFoundError:
                raise click.ClickException("Module not found: {}".format(module))
        directories = list(directories) + module_dirs
        files = list(files) + module_files
        if module_dirs or module_files:
            if not symbols:
                symbols = ["*"]
            site_packages_dirs = site.getsitepackages()
            stdlib_dir = pathlib.Path(pathlib.__file__).parent
            sys_paths = list(site_packages_dirs) + [str(stdlib_dir)] + list(sys_paths)

    if no_init:
        fully_typed = True
    if stdlib and not directories and not files:
        silent = True
    if count or docs:
        signatures = True
    if imports and not symbols:
        signatures = True
    # Show help if no filter options are provided.
    if not any(
        [
            symbols,
            signatures,
            async_,
            unasync,
            function,
            class_,
            documented,
            undocumented,
            public,
            private,
            dunder,
            typed,
            untyped,
            partially_typed,
            fully_typed,
            no_init,
            modules,
        ]
    ):
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()

    if rexec:
        replace = True
        no_file = True
    if replace and signatures:
        raise click.ClickException("--replace cannot be used with --signatures")
    if replace:
        no_file = True
    # If filters were specified without an explicit symbol, use the wildcard.
    if (
        signatures
        or async_
        or unasync
        or function
        or class_
        or documented
        or undocumented
        or public
        or private
        or dunder
        or typed
        or untyped
        or partially_typed
        or fully_typed
        or no_init
        or modules
    ) and not symbols:
        symbols = ["*"]

    # Convert the file/directory/exclude parameters to pathlib.Path objects.
    file_paths = [pathlib.Path(f) for f in files]
    dir_paths = [pathlib.Path(d) for d in directories]
    exclude_paths = [pathlib.Path(e) for e in excludes]

    # Now call the new search() generator to get the results.
    results = list(
        search(
            symbols=list(symbols),
            files=file_paths,
            directories=dir_paths,
            stdlib=stdlib,
            excludes=exclude_paths,
            signatures=signatures,
            no_file=no_file,
            imports=imports,
            modules=list(modules) if modules else None,
            sys_paths=list(sys_paths) if sys_paths else None,
            docs=docs,
            silent=silent,
            function=function,
            async_=async_,
            unasync=unasync,
            class_=class_,
            documented=documented,
            undocumented=undocumented,
            public=public,
            private=private,
            dunder=dunder,
            typed=typed,
            untyped=untyped,
            partially_typed=partially_typed,
            fully_typed=fully_typed,
            no_init=no_init,
        )
    )

    if sum(output_formats) == 0:
        # Regular output: print identifier lines (if any) and snippets.
        for item in results:
            if item.output_identifier_line:
                click.echo(item.output_identifier_line)
            if item.output_import_line:
                click.echo(item.output_import_line)
            click.echo(item.snippet)
            click.echo()
    else:
        fmt = "csv" if csv_ else "tsv" if tsv else "json" if json_ else "nl"
        to_output(
            sys.stdout,
            ((id_prefix + item.symbol_id, item.snippet) for item in results),
            format=fmt,
        )
        return

    if count:
        click.echo(len(results))

    if check and len(results) > 0:
        sys.exit(1)

    if replace:
        # For replacement we require exactly one match.
        if len(results) != 1:
            raise click.ClickException(
                f"--replace only works with a single match, got {len(results)}"
            )
        symbol = results[0]
        if rexec:
            p = subprocess.Popen(
                rexec,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
            )
            stdout, stderr = p.communicate(input=symbol.snippet.encode())
            if p.returncode != 0:
                raise click.ClickException(
                    f"Command '{rexec}' failed with exit code {p.returncode}, stderr: {stderr.decode()}"
                )
            replacement = stdout.decode()
        else:
            if sys.stdin.isatty():
                raise click.ClickException(
                    "--replace only works with text piped to it on stdin"
                )
            new_lines = sys.stdin.readlines()
            if not new_lines:
                raise click.ClickException("No input for --replace found on stdin")
            replacement = "".join(new_lines)
        # Now read the old file content, replace the snippet text, and write it back.
        old_content = symbol.filepath.read_text("utf-8")
        new_content = old_content.replace(symbol.snippet, replacement)
        symbol.filepath.write_text(new_content, "utf-8")
