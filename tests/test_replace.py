from click.testing import CliRunner
from symbex.cli import cli
import pathlib
import pytest
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
