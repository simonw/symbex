# Tests for "symbex -s", using content of example_code.py
import pathlib
import pytest
from click.testing import CliRunner

from symbex.cli import cli


@pytest.fixture
def symbols_text():
    runner = CliRunner()
    args = ["-s", "-f", str(pathlib.Path(__file__).parent / "example_symbols.py")]
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0
    return result.stdout


@pytest.mark.parametrize(
    "name,expected",
    (
        ("func_no_args", "def func_no_args()"),
        ("func_positional_args", "def func_positional_args(a, b, c)"),
        ("async_func", "async def async_func(a, b, c)"),
        ("func_default_args", "def func_default_args(a, b=2, c=3)"),
        ("func_arbitrary_positional_args", "def func_arbitrary_positional_args(*args)"),
        ("func_arbitrary_keyword_args", "def func_arbitrary_keyword_args(**kwargs)"),
        ("func_arbitrary_args", "def func_arbitrary_args(*args, **kwargs)"),
        ("func_positional_only_args", "def func_positional_only_args(a, /, b, c)"),
        ("func_keyword_only_args", "def func_keyword_only_args(a, *, b, c)"),
        ("func_type_annotations", "def func_type_annotations(a: int, b: str) -> bool"),
        ("ClassNoBase", "class ClassNoBase"),
        ("ClassSingleBase", "class ClassSingleBase(int)"),
        ("ClassMultipleBase", "class ClassMultipleBase(int, str)"),
        ("ClassWithMeta", "class ClassWithMeta(metaclass=type)"),
    ),
)
def test_symbols(name, expected, symbols_text):
    # For error reporting try and find the relevant bit
    likely_line = [
        line
        for line in symbols_text.split("\n")
        if (f"{name}(" in line or line.startswith(f"class {name}"))
    ][0]
    assert expected in symbols_text, "\nexpected:\t{}\ngot:\t\t{}".format(
        expected, likely_line
    )
    # Special case to ensure we don't get ClassNoBase()
    assert "ClassNoBase()" not in symbols_text


def test_method_symbols():
    runner = CliRunner()
    args = [
        "*.async*",
        "-s",
        "-f",
        str(pathlib.Path(__file__).parent / "example_symbols.py"),
    ]
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0
    assert result.stdout == (
        "# File: tests/example_symbols.py Class: ClassWithMethods Line: 88\n"
        "    async def async_method(a, b, c)\n"
        "\n"
    )
