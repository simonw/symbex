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
        # This doesn't make sense, so should return []
        (
            ["--async", "--class"],
            [],
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
        (
            ["--typed", "--async"],
            [
                "async def async_func_fully_typed",
            ],
        ),
        (
            ["--untyped"],
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
            ],
        ),
        (
            ["--partially-typed"],
            [
                "def func_partially_typed",
                "def func_partially_typed_no_typed_return",
                "def func_partially_typed_only_typed_return",
            ],
        ),
        (
            ["--fully-typed"],
            [
                "def func_type_annotations",
                "def function_with_non_pep_0484_annotation",
                "def complex_annotations",
                "def func_fully_typed",
                "async def async_func_fully_typed",
                "def func_typed_no_params",
            ],
        ),
        # Test against methods
        (
            ["--typed", "*.*"],
            [
                "def method_types",
                "def __init__",
                "def method_fully_typed",
                "def method_partially_typed",
            ],
        ),
        (
            ["--untyped", "*.*"],
            [
                "def __init__",
                "def method_positional_only_args",
                "def method_keyword_only_args",
                "async def async_method",
                "def method_untyped",
            ],
        ),
        (
            ["--fully-typed", "*.*"],
            ["def method_types", "def __init__", "def method_fully_typed"],
        ),
        (
            ["--fully-typed", "--no-init", "*.*"],
            [
                "def method_types",
                "def method_fully_typed",
            ],
        ),
        (
            ["--partially-typed", "*.*"],
            ["def method_partially_typed"],
        ),
        # Documented and undocumented
        (
            ["--documented"],
            [
                "def func_no_args",
                "def func_positional_args",
            ],
        ),
        (
            ["--undocumented", "func_arbitrary_*"],
            [
                "def func_arbitrary_positional_args",
                "def func_arbitrary_keyword_args",
                "def func_arbitrary_args",
            ],
        ),
        (
            ["--documented", "*.*"],
            [
                "def method_fully_typed",
                "def method_partially_typed",
            ],
        ),
        (
            ["--undocumented", "*.method_*"],
            [
                "def method_types",
                "def method_positional_only_args",
                "def method_keyword_only_args",
                "def method_untyped",
            ],
        ),
    ),
)
def test_filters(args, expected):
    runner = CliRunner()
    full_args = args + [
        "-s",
        "-f",
        str(pathlib.Path(__file__).parent / "example_symbols.py"),
    ]
    result = runner.invoke(
        cli,
        full_args,
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

    # Test the --count option too
    expected_count = len(expected)
    result2 = runner.invoke(
        cli,
        full_args + ["--count"],
        catch_exceptions=False,
    )
    assert result2.exit_code == 0
    assert result2.stdout.strip() == str(expected_count)
