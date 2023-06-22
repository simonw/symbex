# Tests for "symbex --imports --sys-path ..."
import pathlib
import pytest
from click.testing import CliRunner

from symbex.cli import cli


@pytest.fixture
def imports_dir(tmpdir):
    for path, content in (
        ("one/foo.py", "def foo1():\n    pass"),
        ("one/bar.py", "def bar1():\n    pass"),
        ("two/foo.py", "def foo2():\n    pass"),
        ("two/bar.py", "def bar2():\n    pass"),
        ("deep/nested/three/foo.py", "def foo3():\n    pass"),
        (
            "deep/nested/three/bar.py",
            ("class Bar3:\n" "    def __init__(self):\n" "        pass"),
        ),
    ):
        p = pathlib.Path(tmpdir / path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, "utf-8")
    return tmpdir


@pytest.mark.parametrize(
    "args,sys_path,expected",
    (
        (["foo1"], None, "from one.foo import foo1"),
        (["foo2"], None, "from two.foo import foo2"),
        (["foo1"], "one/", "from foo import foo1"),
        # This should force a relative import:
        (["foo2"], "one/", "from .foo import foo2"),
        # Various deep nested examples
        (["foo3"], None, "from deep.nested.three.foo import foo3"),
        (["Bar3"], None, "from deep.nested.three.bar import Bar3"),
        (["foo3"], "deep/nested", "from three.foo import foo3"),
        # Test display of methods
        (["Bar3.*"], "deep/nested", "from three.bar import Bar3"),
    ),
)
def test_imports(args, sys_path, expected, imports_dir):
    runner = CliRunner()
    args = ["-in", "-d", str(imports_dir)] + args
    if sys_path:
        args.extend(("--sys-path", str(imports_dir / sys_path)))
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0
    import_line = [
        line[2:] for line in result.stdout.split("\n") if line.startswith("# from")
    ][0]
    assert import_line == expected
