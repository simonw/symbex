# Tests for "symbex --async / --class / --typed etc"
import pathlib
import pytest
from click.testing import CliRunner

from symbex.cli import cli


@pytest.mark.parametrize(
    "args,expected",
    (
        (
            ["--function"],
            [
                "def func_no_args",
                "def func_positional_args",
                "async def async_func",
                "def func_default_args",
                "def func_arbitrary_positional_args",
                "def func_arbitrary_keyword_args",
                "def func_arbitrary_args",
                "def func_positional_only_args",
                "def func_keyword_only_args",
                "def func_type_annotations",
                "def function_with_non_pep_0484_annotation",
                "def complex_annotations",
                "def func_fully_typed",
                "async def async_func_fully_typed",
                "def func_partially_typed",
                "def func_partially_typed_no_typed_return",
                "def func_partially_typed_only_typed_return",
                "def func_typed_no_params",
            ],
        ),
        (
            ["--class"],
            [
                "class ClassNoBase",
                "class ClassSingleBase",
                "class ClassMultipleBase",
                "class ClassWithMeta",
                "class ClassWithMethods",
                "class ClassForTypedTests",
            ],
        ),
        (
            ["--async"],
            [
                "async def async_func",
                "async def async_func_fully_typed",
            ],
        ),
        # Using multiple at the same time returns symbols matching any of them
        (
            ["--async", "--class"],
            [
                "async def async_func",
                "class ClassNoBase",
                "class ClassSingleBase",
                "class ClassMultipleBase",
                "class ClassWithMeta",
                "class ClassWithMethods",
                "async def async_func_fully_typed",
                "class ClassForTypedTests",
            ],
        ),
        # Various typing options
        (
            ["--typed"],
            [
                "def func_type_annotations",
                "def function_with_non_pep_0484_annotation",
                "def complex_annotations",
                "def func_fully_typed",
                "async def async_func_fully_typed",
                "def func_partially_typed",
                "def func_partially_typed_no_typed_return",
                "def func_partially_typed_only_typed_return",
                "def func_typed_no_params",
            ],
        ),
    ),
)
def test_filters(args, expected):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        args
        + [
            "-s",
            "-f",
            str(pathlib.Path(__file__).parent / "example_symbols.py"),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    # Remove # File: lines and blank lines
    lines = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and not line.startswith("# File:")
    ]
    # We only match up to the opening "("
    defs = [line.split("(")[0] for line in lines]
    assert defs == expected
