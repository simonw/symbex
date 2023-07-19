import ast
import click
import importlib
import inspect
import pathlib
import site
import subprocess
import sys

from .lib import (
    code_for_node,
    find_symbol_nodes,
    import_line_for_function,
    read_file,
    type_summary,
)


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
        directories = [*directories, *module_dirs]
        files = [*files, *module_files]
        if module_dirs or module_files:
            if not symbols:
                symbols = ["*"]
            site_packages_dirs = site.getsitepackages()
            stdlib_dir = pathlib.Path(pathlib.__file__).parent
            sys_paths = [*site_packages_dirs, str(stdlib_dir), *sys_paths]

    if no_init:
        fully_typed = True
    if stdlib and not directories and not files:
        silent = True
    if stdlib:
        stdlib_folder = pathlib.Path(pathlib.__file__).parent.resolve()
        directories = [*directories, *[stdlib_folder]]
        if str(stdlib_folder) not in sys_paths:
            sys_paths = [*[str(stdlib_folder)], *sys_paths]
    if count or docs:
        signatures = True
    if imports and not symbols:
        signatures = True
    # Show --help if no filter options are provided:
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
    # Default to '*' if --signatures or filters are provided without symbols
    if (
        any(
            [
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
        )
        and not symbols
    ):
        symbols = ["*"]
    if not files and not directories:
        directories = ["."]

    excludes = [pathlib.Path(exclude) for exclude in excludes]

    def iterate_files():
        yield from (pathlib.Path(f) for f in files)
        for directory in directories:
            for path in pathlib.Path(directory).rglob("*.py"):
                # Skip if path is inside any of 'excludes'
                if any(is_subpath(path, exclude) for exclude in excludes):
                    continue
                if path.is_file():
                    yield path

    # If any --filters were supplied, handle them:
    if any(
        [
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
        ]
    ):
        # Return just nodes matching filters
        def filter(node: ast.AST) -> bool:
            # Filters must ALL match
            if async_ and not isinstance(node, ast.AsyncFunctionDef):
                return False
            if function and not isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
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
            # if no summary, type filters all fail
            if not summary and (
                typed or untyped or partially_typed or fully_typed or no_init
            ):
                return False
            # Apply type filters
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

    else:
        # All nodes are allowed
        def filter(node: ast.AST) -> bool:
            return True

    pwd = pathlib.Path(".").resolve()
    num_matches = 0
    replace_matches = []
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
            if not filter(node):
                continue
            if count or check:
                num_matches += 1
                if count or not signatures:
                    continue
            # If file is within pwd, print relative path
            if pwd in file.resolve().parents:
                path = file.resolve().relative_to(pwd)
            else:
                # else print absolute path
                path = file.resolve()
            snippet, line_no = code_for_node(code, node, class_name, signatures, docs)
            if replace:
                replace_matches.append((file.resolve(), snippet, line_no))
                continue
            if not no_file:
                bits = ["# File:", path]
                if class_name:
                    bits.extend(["Class:", class_name])
                bits.extend(["Line:", line_no])
                click.echo(" ".join(str(bit) for bit in bits))
            if imports:
                import_line = import_line_for_function(
                    node.name, path, sys_paths or directories
                )
                # If it's a class then output '# from x import Class' instead
                if class_name:
                    import_line = (
                        import_line.split(" import ")[0] + " import " + class_name
                    )
                click.echo("# " + import_line)
            click.echo(snippet)
            click.echo()
    if count:
        click.echo(num_matches)

    if check and num_matches > 0:
        sys.exit(1)

    if replace:
        # Only works if we got a single match
        if len(replace_matches) != 1:
            raise click.ClickException(
                "--replace only works with a single match, got {}".format(
                    len(replace_matches)
                )
            )
        filepath, to_replace = replace_matches[0][:2]
        if rexec:
            # Run to_replace through that command
            p = subprocess.Popen(
                rexec,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
            )
            stdout, stderr = p.communicate(input=to_replace.encode())
            if p.returncode != 0:
                raise click.ClickException(
                    f"Command '{rexec}' failed with exit code {p.returncode}"
                    f", stderr: {stderr.decode()}"
                )

            replacement = stdout.decode()
        else:
            if sys.stdin.isatty():
                raise click.ClickException(
                    "--replace only works with text piped to it on stdin"
                )
            new_lines = sys.stdin.readlines()
            # Check if any lines were read
            if len(new_lines) == 0:
                raise click.ClickException("No input for --replace found on stdin")
            replacement = "".join(new_lines)
        old = filepath.read_text("utf-8")
        new = old.replace(to_replace, replacement)
        filepath.write_text(new, "utf-8")


def is_subpath(path: pathlib.Path, parent: pathlib.Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def is_dunder(name):
    return name.startswith("__") and name.endswith("__")
