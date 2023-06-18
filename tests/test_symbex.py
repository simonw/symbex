import pathlib
import pytest
from click.testing import CliRunner

from symbex.cli import cli


@pytest.fixture
def directory_full_of_code(tmpdir):
    for path, content in (
        ("foo.py", "def foo1():\n    pass\n\n@decorated\ndef foo2():\n    pass\n\n"),
        ("bar.py", "class BarClass:\n    pass\n\n"),
        ("nested/baz.py", "def baz():\n    pass\n\n"),
    ):
        p = pathlib.Path(tmpdir / path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, "utf-8")
    return tmpdir


@pytest.mark.parametrize(
    "args,expected",
    (
        (["foo1"], "# File: foo.py Line: 1\ndef foo1():\n    pass\n\n"),
        (
            ["foo*"],
            "# File: foo.py Line: 1\ndef foo1():\n    pass\n\n# File: foo.py Line: 4\n@decorated\ndef foo2():\n    pass\n\n",
        ),
        (["BarClass"], "# File: bar.py Line: 1\nclass BarClass:\n    pass\n\n"),
        (["baz"], "# File: nested/baz.py Line: 1\ndef baz():\n    pass\n\n"),
    ),
)
def test_fixture(directory_full_of_code, args, expected, monkeypatch):
    runner = CliRunner()
    monkeypatch.chdir(directory_full_of_code)
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0
    assert result.stdout == expected
