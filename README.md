# py-grep

[![PyPI](https://img.shields.io/pypi/v/py-grep.svg)](https://pypi.org/project/py-grep/)
[![Changelog](https://img.shields.io/github/v/release/simonw/py-grep?include_prereleases&label=changelog)](https://github.com/simonw/py-grep/releases)
[![Tests](https://github.com/simonw/py-grep/workflows/Test/badge.svg)](https://github.com/simonw/py-grep/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/py-grep/blob/master/LICENSE)

Find the Python code for specified symbols

## Installation

Install this tool using `pip`:
```bash
pip install py-grep
```
## Usage

`py-grep` can search for names of functions and classes that occur at the top level of a Python file.

To search every `.py` file in your current directory and all subdirectories, run like this:

```bash
py-grep my_function
```
You can search for more than one symbol at a time:
```bash
py-grep my_function MyClass
```
To search within a specific file, pass that file using the `-f` option. You can pass this more than once to search multiple files.

```bash
py-grep MyClass -f my_file.py
```
To search within a specific directory and all of its subdirectories, use the `-d` option:
```bash
py-grep Database -d ~/projects/datasette
```

## Example output

In a fresh checkout of [Datasette](https://github.com/simonw/datasette) I ran this command:

```bash
py-grep MessagesDebugView get_long_description
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

## Using with LLM

This tool is primarily designed to be used with [LLM](https://llm.datasette.io/), a CLI tool for working with Large Language Models.

`py-grep` makes it easy to grab a specific class or function and pass it to the `llm` command.

For example, I ran this in the Datasette repository root:

```bash
py-grep Response | llm --system 'Explain this code, succinctly'
```
And got back this:

> This code defines a custom `Response` class with methods for returning HTTP responses. It includes methods for setting cookies, returning HTML, text, and JSON responses, and redirecting to a different URL. The `asgi_send` method sends the response to the client using the ASGI (Asynchronous Server Gateway Interface) protocol.


## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:
```bash
cd py-grep
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