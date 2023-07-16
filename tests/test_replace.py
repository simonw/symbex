from click.testing import CliRunner
from symbex.cli import cli
import pathlib
import pytest
import sys
from unittest.mock import patch
import yaml


@pytest.mark.parametrize(
    "test", yaml.safe_load(open(pathlib.Path(__file__).parent / "replace_tests.yaml"))
)
def test_replace(test):
    original, stdin, args, expected = (
        test["original"],
        test["stdin"],
        test["args"],
        test["expected"],
    )
    runner = CliRunner()
    with runner.isolated_filesystem() as root:
        path = pathlib.Path(root) / "code.py"
        path.write_text(original, "utf-8")
        result = runner.invoke(cli, args, input=stdin, catch_exceptions=False)
        modified = path.read_text("utf-8")
    assert result.exit_code == 0
    assert modified.strip() == expected.strip()


@pytest.mark.parametrize(
    "files,args,error",
    (
        (
            {"foo.py": "def bar(): pass"},
            ["baz"],
            "Error: --replace only works with a single match, got 0",
        ),
        (
            {"foo.py": "def bar(): pass", "baz/foo.py": "def bar(): pass"},
            ["bar"],
            "Error: --replace only works with a single match, got 2",
        ),
        (
            {"foo.py": "def bar(): pass"},
            ["bar", "-s"],
            "Error: --replace cannot be used with --signatures",
        ),
        (
            {"foo.py": "def bar(): pass"},
            ["bar"],
            "Error: No input for --replace found on stdin",
        ),
    ),
)
def test_replace_errors(files, args, error):
    runner = CliRunner()
    with patch("symbex.cli.sys.stdin.isatty", return_value=True):
        with runner.isolated_filesystem() as root:
            root = pathlib.Path(root)
            for path, code in files.items():
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_text(code, "utf-8")
            result = runner.invoke(cli, args + ["--replace"], catch_exceptions=False)
    assert result.exit_code == 1
    assert result.output.strip() == error


INPUT_CODE = """
def foo(bar):
    return 1 + 2 + 3

class Foo:
    def bar(self):
        return 1 + 2 + 3
"""
REXEC_EXPECTED = """
DEF FOO(BAR):
    RETURN 1 + 2 + 3


class Foo:
    def bar(self):
        return 1 + 2 + 3
"""

TO_UPPER = """
import sys

print(sys.stdin.read().upper())
"""


def test_replace_rexec():
    runner = CliRunner()
    with runner.isolated_filesystem() as root:
        path = pathlib.Path(root) / "code.py"
        path.write_text(INPUT_CODE, "utf-8")
        to_upper = pathlib.Path(root) / "to_upper.py"
        to_upper.write_text(TO_UPPER, "utf-8")
        long_command = " ".join(
            [
                sys.executable,
                str(to_upper),
            ]
        )
        args = ["foo", "--rexec", long_command]
        result = runner.invoke(cli, args, catch_exceptions=False)
        modified = path.read_text("utf-8")
    assert result.exit_code == 0
    assert modified.strip() == REXEC_EXPECTED.strip()


def test_replace_rexec_error():
    runner = CliRunner()
    with runner.isolated_filesystem() as root:
        path = pathlib.Path(root) / "code.py"
        path.write_text(INPUT_CODE, "utf-8")
        to_upper = pathlib.Path(root) / "to_upper.py"
        to_upper.write_text("exit(1)", "utf-8")
        long_command = " ".join(
            [
                sys.executable,
                str(to_upper),
            ]
        )
        args = ["foo", "--rexec", long_command]
        result = runner.invoke(cli, args, catch_exceptions=False)
        not_modified = path.read_text("utf-8")
    assert result.exit_code == 1
    assert not_modified.strip() == INPUT_CODE.strip()
