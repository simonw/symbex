# symbex

[![PyPI](https://img.shields.io/pypi/v/symbex.svg)](https://pypi.org/project/symbex/)
[![Changelog](https://img.shields.io/github/v/release/simonw/symbex?include_prereleases&label=changelog)](https://github.com/simonw/symbex/releases)
[![Tests](https://github.com/simonw/symbex/workflows/Test/badge.svg)](https://github.com/simonw/symbex/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/symbex/blob/master/LICENSE)

Find the Python code for specified symbols

Read [symbex: search Python code for functions and classes, then pipe them into a LLM](https://simonwillison.net/2023/Jun/18/symbex/) for background on this project.

## Installation

Install this tool using `pip`:
```bash
pip install symbex
```
## Usage

`symbex` can search for names of functions and classes that occur at the top level of a Python file.

To search every `.py` file in your current directory and all subdirectories, run like this:

```bash
symbex my_function
```
You can search for more than one symbol at a time:
```bash
symbex my_function MyClass
```
Wildcards are supported - to search for every `test_` function run this (note the single quotes to avoid the shell interpreting the `*` as a wildcard):
```bash
symbex 'test_*'
```
To search for methods within classes, use `class.method` notation:
```bash
symbex Entry.get_absolute_url
```
Wildcards are supported here as well:
```bash
symbex 'Entry.*'
symbex '*.get_absolute_url'
symbex '*.get_*'
```
Or to view every method of every class:
```bash
symbex '*.*'
```
To search within a specific file, pass that file using the `-f` option. You can pass this more than once to search multiple files.

```bash
symbex MyClass -f my_file.py
```
To search within a specific directory and all of its subdirectories, use the `-d` option:
```bash
symbex Database -d ~/projects/datasette
```
If `symbex` encounters any Python code that it cannot parse, it will print a warning message and continue searching:
```
# Syntax error in path/badcode.py: expected ':' (<unknown>, line 1)
```
Pass `--silent` to suppress these warnings:
```bash
symbex MyClass --silent
```
### Filters

In addition to searching for symbols, you can apply filters to the results.

The following filters are available:

- `--function` - only functions
- `--class` - only classes
- `--async` - only `async def` functions
- `--documented` - functions/classes that have a docstring
- `--undocumented` - functions/classes that do not have a docstring
- `--typed` - functions that have at least one type annotation
- `--untyped` - functions that have no type annotations
- `--partially-typed` - functions that have some type annotations but not all
- `--fully-typed` - functions that have type annotations for every argument and the return value

For example, to see the signatures of every `async def` function in your project that doesn't have any type annotations:

```bash
symbex -s --async --untyped
```

For class methods instead of functions, you can combine filters with a symbol search argument of `*.*`.

This example shows the full source code of every class method in your project with type annotations on all of the arguments and the return value:

```bash
symbex --fully-typed '*.*'
```

### Example output

In a fresh checkout of [Datasette](https://github.com/simonw/datasette) I ran this command:

```bash
symbex MessagesDebugView get_long_description
```
Here's the output of the command:
```
# File: setup.py Line: 5
def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()

# File: datasette/views/special.py Line: 60
class PatternPortfolioView(View):
    async def get(self, request, datasette):
        await datasette.ensure_permissions(request.actor, ["view-instance"])
        return Response.html(
            await datasette.render_template(
                "patterns.html",
                request=request,
                view_name="patterns",
            )
        )
```
### Just the signatures

The `-s/--signatures` option will list just the signatures of the functions and classes, for example:
```bash
symbex -s -d symbex
```
<!-- [[[cog
import cog
from click.testing import CliRunner
import pathlib
from symbex.cli import cli

path = pathlib.Path("symbex").resolve()
runner = CliRunner()
result = runner.invoke(cli, ["-s", "-d", str(path)])
# Need a consistent sort order
chunks = result.stdout.strip().split("\n\n")
chunks.sort()
cog.out(
    "```python\n{}\n```\n".format("\n\n".join(chunks))
)
]]] -->
```python
# File: symbex/cli.py Line: 95
def cli(symbols, files, directories, signatures, docstrings, count, silent, async_, function, class_, documented, undocumented, typed, untyped, partially_typed, fully_typed)

# File: symbex/lib.py Line: 105
def function_definition(function_node: AST)

# File: symbex/lib.py Line: 12
def find_symbol_nodes(code: str, filename: str, symbols: Iterable[str]) -> List[Tuple[(AST, Optional[str])]]

# File: symbex/lib.py Line: 173
def class_definition(class_def)

# File: symbex/lib.py Line: 207
def annotation_definition(annotation: AST) -> str

# File: symbex/lib.py Line: 225
def read_file(path)

# File: symbex/lib.py Line: 251
class TypeSummary

# File: symbex/lib.py Line: 256
def type_summary(node: AST) -> Optional[TypeSummary]

# File: symbex/lib.py Line: 302
def quoted_string(s)

# File: symbex/lib.py Line: 36
def code_for_node(code: str, node: AST, class_name: str, signatures: bool, docstrings: bool) -> Tuple[(str, int)]

# File: symbex/lib.py Line: 70
def add_docstring(definition: str, node: AST, docstrings: bool, is_method: bool) -> str

# File: symbex/lib.py Line: 80
def match(name: str, symbols: Iterable[str]) -> bool
```
<!-- [[[end]]] -->
This can be combined with other options, or you can run `symbex -s` to see every symbol in the current directory and its subdirectories.

To include docstrings in those signatures, use `--docstrings`:
```bash
symbex --docstrings --documented -f symbex/lib.py
```

<!-- [[[cog
runner = CliRunner()
result = runner.invoke(cli, ["--docstrings", "--documented", "-f", str(path / "lib.py")])
# Need a consistent sort order
chunks = result.stdout.strip().split("\n\n")
chunks.sort()
cog.out(
    "```python\n{}\n```\n".format("\n\n".join(chunks))
)
]]] -->
```python
# File: symbex/lib.py Line: 12
def find_symbol_nodes(code: str, filename: str, symbols: Iterable[str]) -> List[Tuple[(AST, Optional[str])]]
    "Returns ast Nodes matching symbols"

# File: symbex/lib.py Line: 36
def code_for_node(code: str, node: AST, class_name: str, signatures: bool, docstrings: bool) -> Tuple[(str, int)]
    "Returns the code for a given node"

# File: symbex/lib.py Line: 80
def match(name: str, symbols: Iterable[str]) -> bool
    "Returns True if name matches any of the symbols, resolving wildcards"
```
<!-- [[[end]]] -->

## Counting symbols

If you just want to count the number of functions and classes that match your filters, use the `--count` option. Here's how to count your classes:

```bash
symbex --class --count
```
Or to count every async test function:
```bash
symbex --async 'test_*' --count
```

## Using with LLM

This tool is primarily designed to be used with [LLM](https://llm.datasette.io/), a CLI tool for working with Large Language Models.

`symbex` makes it easy to grab a specific class or function and pass it to the `llm` command.

For example, I ran this in the Datasette repository root:

```bash
symbex Response | llm --system 'Explain this code, succinctly'
```
And got back this:

> This code defines a custom `Response` class with methods for returning HTTP responses. It includes methods for setting cookies, returning HTML, text, and JSON responses, and redirecting to a different URL. The `asgi_send` method sends the response to the client using the ASGI (Asynchronous Server Gateway Interface) protocol.

## Similar tools

- [pyastgrep](https://github.com/spookylukey/pyastgrep) by Luke Plant offers advanced capabilities for viewing and searching through Python ASTs using XPath.
- [cq](https://github.com/fullstackio/cq) is a tool thet lets you "extract code snippets using CSS-like selectors", built using [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) and primarily targetting JavaScript and TypeScript.

## symbex --help

<!-- [[[cog
import cog
result2 = runner.invoke(cli, ["--help"])
help = result2.output.replace("Usage: cli", "Usage: symbex")
cog.out(
    "```\n{}\n```".format(help)
)
]]] -->
```
Usage: symbex [OPTIONS] [SYMBOLS]...

  Find symbols in Python code and print the code for them.

  Example usage:

      # Search current directory and subdirectories
      symbex my_function MyClass

      # Search using a wildcard
      symbex 'test_*'

      # Find a specific class method
      symbex 'MyClass.my_method'

      # Find class methods using wildcards
      symbex '*View.handle_*'

      # Search a specific file
      symbex MyClass -f my_file.py

      # Search within a specific directory and its subdirectories
      symbex Database -d ~/projects/datasette

      # View signatures for all symbols in current directory and subdirectories
      symbex -s

      # View signatures for all test functions
      symbex 'test_*' -s

      # View signatures for all async functions with type definitions
      symbex --async --typed -s

      # Count the number of --async functions in the project
      symbex --async --count

Options:
  --version                  Show the version and exit.
  -f, --file FILE            Files to search
  -d, --directory DIRECTORY  Directories to search
  -s, --signatures           Show just function and class signatures
  --docstrings               Show function and class signatures plus docstrings
  --count                    Show count of matching symbols
  --silent                   Silently ignore Python files with parse errors
  --async                    Filter async functions
  --function                 Filter functions
  --class                    Filter classes
  --documented               Filter functions with docstrings
  --undocumented             Filter functions without docstrings
  --typed                    Filter functions with type annotations
  --untyped                  Filter functions without type annotations
  --partially-typed          Filter functions with partial type annotations
  --fully-typed              Filter functions with full type annotations
  --help                     Show this message and exit.

```
<!-- [[[end]]] -->

## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:
```bash
cd symbex
python -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
pytest
```
### just

You can also install [just](https://github.com/casey/just) and use it to run the tests and linters like this:

```bash
just
```
Or to list commands:
```bash
just -l
```
```
Available recipes:
    black         # Apply Black
    cog           # Rebuild docs with cog
    default       # Run tests and linters
    lint          # Run linters
    test *options # Run pytest with supplied options
```
