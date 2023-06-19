# symbex

[![PyPI](https://img.shields.io/pypi/v/symbex.svg)](https://pypi.org/project/symbex/)
[![Changelog](https://img.shields.io/github/v/release/simonw/symbex?include_prereleases&label=changelog)](https://github.com/simonw/symbex/releases)
[![Tests](https://github.com/simonw/symbex/workflows/Test/badge.svg)](https://github.com/simonw/symbex/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/symbex/blob/master/LICENSE)

Find the Python code for specified symbols

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
    "```\n{}\n```\n".format("\n\n".join(chunks))
)
]]] -->
```
# File: symbex/cli.py Line: 37
def cli(symbols, files, directories, signatures, silent)

# File: symbex/lib.py Line: 161
def class_definition(class_def)

# File: symbex/lib.py Line: 32
def code_for_node(code: str, node: AST, class_name: str, signatures: bool)

# File: symbex/lib.py Line: 63
def match(name: str, symbols) -> bool

# File: symbex/lib.py Line: 8
def find_symbol_nodes(code: str, symbols)

# File: symbex/lib.py Line: 88
def function_definition(function_node: AST)
```
<!-- [[[end]]] -->
This can be combined with other options, or you can run `symbex -s` to see every symbol in the current directory and its subdirectories.

## Using with LLM

This tool is primarily designed to be used with [LLM](https://llm.datasette.io/), a CLI tool for working with Large Language Models.

`symbex` makes it easy to grab a specific class or function and pass it to the `llm` command.

For example, I ran this in the Datasette repository root:

```bash
symbex Response | llm --system 'Explain this code, succinctly'
```
And got back this:

> This code defines a custom `Response` class with methods for returning HTTP responses. It includes methods for setting cookies, returning HTML, text, and JSON responses, and redirecting to a different URL. The `asgi_send` method sends the response to the client using the ASGI (Asynchronous Server Gateway Interface) protocol.


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
