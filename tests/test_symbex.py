import pathlib
import pytest
import textwrap
from click.testing import CliRunner

from symbex.cli import cli
from symbex.lib import read_file, quoted_string


def test_no_args_shows_help():
    runner = CliRunner()
    result = runner.invoke(cli, catch_exceptions=False)
    assert result.exit_code == 0
    assert "Usage: cli [OPTIONS]" in result.stdout


@pytest.fixture
def directory_full_of_code(tmpdir):
    for path, content in (
        ("foo.py", "def foo1():\n    pass\n\n@decorated\ndef foo2():\n    pass\n\n"),
        ("bar.py", "class BarClass:\n    pass\n\n"),
        ("nested.py/x/baz.py", 'def baz(delimiter=", ", type=str):\n    pass\n\n'),
        ("nested.py/error.py", "def baz_error()" + "bug:\n    pass\n\n"),
        (
            "methods.py",
            textwrap.dedent(
                """
        class MyClass:
            def __init__(self, a):
                self.a = a

            def method1(self, a=1):
                pass
        """
            ),
        ),
        (
            "async.py",
            textwrap.dedent(
                """
            async def async_func(a, b, c):
                pass

            class MyAsyncClass:
                async def async_method(a, b, c):
                    pass
            """
            ).strip(),
        ),
    ):
        p = pathlib.Path(tmpdir / path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, "utf-8")
    return tmpdir


@pytest.mark.parametrize(
    "args,expected",
    (
        (["foo1", "--silent"], "# File: foo.py Line: 1\ndef foo1():\n    pass\n\n"),
        (
            ["foo*", "--silent"],
            "# File: foo.py Line: 1\ndef foo1():\n    pass\n\n# File: foo.py Line: 4\n@decorated\ndef foo2():\n    pass\n\n",
        ),
        (
            ["BarClass", "--silent"],
            "# File: bar.py Line: 1\nclass BarClass:\n    pass\n\n",
        ),
        (
            ["baz", "--silent"],
            '# File: nested.py/x/baz.py Line: 1\ndef baz(delimiter=", ", type=str):\n    pass\n\n',
        ),
        (
            ["async_func", "--silent"],
            "# File: async.py Line: 1\nasync def async_func(a, b, c):\n    pass\n\n",
        ),
        # The -f option
        (
            ["baz", "-f", "nested.py/x/baz.py", "--silent"],
            '# File: nested.py/x/baz.py Line: 1\ndef baz(delimiter=", ", type=str):\n    pass\n\n',
        ),
        # The -d option
        (
            ["baz", "-d", "nested.py", "--silent"],
            '# File: nested.py/x/baz.py Line: 1\ndef baz(delimiter=", ", type=str):\n    pass\n\n',
        ),
        # The -d option with -x to exclude
        (
            ["baz", "-d", "nested.py", "-x", "nested.py/x/", "--silent"],
            "",
        ),
        # Classes
        (
            ["MyClass", "--silent"],
            "# File: methods.py Line: 2\n"
            "class MyClass:\n"
            "    def __init__(self, a):\n"
            "        self.a = a\n"
            "\n"
            "    def method1(self, a=1):\n"
            "        pass\n"
            "\n",
        ),
        (
            ["MyClass.__init__", "--silent"],
            "# File: methods.py Class: MyClass Line: 3\n"
            "    def __init__(self, a):\n"
            "        self.a = a\n"
            "\n",
        ),
        (
            ["MyClass.*", "--silent"],
            "# File: methods.py Class: MyClass Line: 3\n"
            "    def __init__(self, a):\n"
            "        self.a = a\n"
            "\n"
            "# File: methods.py Class: MyClass Line: 6\n"
            "    def method1(self, a=1):\n"
            "        pass\n"
            "\n",
        ),
        (
            ["*.method*", "--silent"],
            "# File: methods.py Class: MyClass Line: 6\n"
            "    def method1(self, a=1):\n"
            "        pass\n"
            "\n",
        ),
        (
            ["*.async_method", "--silent"],
            (
                "# File: async.py Class: MyAsyncClass Line: 5\n"
                "    async def async_method(a, b, c):\n"
                "        pass\n"
                "\n"
            ),
        ),
    ),
)
def test_fixture(directory_full_of_code, monkeypatch, args, expected):
    runner = CliRunner()
    monkeypatch.chdir(directory_full_of_code)
    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0
    assert result.stdout == expected


@pytest.mark.parametrize(
    "args,expected",
    (
        (
            ["foo*", "--silent"],
            "# File: foo.py Line: 1\n"
            "def foo1()\n"
            "\n"
            "# File: foo.py Line: 5\n"
            "def foo2()",
        ),
        (["BarClass", "--silent"], "# File: bar.py Line: 1\n" "class BarClass"),
        (
            ["baz", "--silent"],
            (
                "# File: nested.py/x/baz.py Line: 1\n"
                'def baz(delimiter=", ", type=str)'
            ),
        ),
        # Test for the --module option
        (
            ["-m", "pathlib", "Path", "--silent", "-in"],
            ("# from pathlib import Path\nclass Path(PurePath)"),
        ),
    ),
)
def test_symbex_symbols(directory_full_of_code, monkeypatch, args, expected):
    runner = CliRunner()
    monkeypatch.chdir(directory_full_of_code)
    result = runner.invoke(cli, args + ["-s"], catch_exceptions=False)
    assert result.exit_code == 0
    # Here expected is just the first two lines
    assert result.stdout.strip() == expected


def test_errors(directory_full_of_code, monkeypatch):
    # Test without --silent to see errors
    runner = CliRunner(mix_stderr=False)
    monkeypatch.chdir(directory_full_of_code)
    result = runner.invoke(cli, ["baz"], catch_exceptions=False)
    assert result.exit_code == 0
    expected = (
        "# File: nested.py/x/baz.py Line: 1\n"
        'def baz(delimiter=", ", type=str):\n'
        "    pass\n\n"
    )
    assert result.stdout == expected
    # This differs between different Python versions
    assert result.stderr.startswith("# Syntax error in nested.py/error.py:")


def test_read_file_with_encoding(tmpdir):
    # https://github.com/simonw/symbex/issues/18#issuecomment-1597546242
    path = tmpdir / "encoded.py"
    path.write_binary(
        b"# coding: iso-8859-5\n# (Unlikely to be the default encoding for most testers.)\n"
        b"# \xb1\xb6\xff\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef <- Cyrillic characters\n"
        b'u = "\xae\xe2\xf0\xc4"\n'
    )
    text = read_file(path)
    assert text == (
        "# coding: iso-8859-5\n"
        "# (Unlikely to be the default encoding for most testers.)\n"
        "# БЖџрстуфхцчшщъыьэюя <- Cyrillic characters\n"
        'u = "Ўт№Ф"\n'
    )


def test_quoted_string():
    # Single line, no quotes
    assert quoted_string("Hello, World!") == '"Hello, World!"'

    # Single line, with quotes
    assert quoted_string('Hello, "World"!') == '"Hello, \\"World\\"!"'

    # Multiline, no quotes
    multiline_str = "Hello,\nWorld!"
    expected_result = '"""Hello,\nWorld!"""'
    assert quoted_string(multiline_str) == expected_result

    # Multiline, with triple quotes
    multiline_str = '''Hello,
"World",
Here are some triple quotes: """ '''
    expected_multiline_result = (
        '"""Hello,\n"World",\nHere are some triple quotes: \\"\\"\\" """'
    )
    quoted_multiline_result = quoted_string(multiline_str)
    assert quoted_multiline_result == expected_multiline_result

    # Empty string
    assert quoted_string("") == '""'
