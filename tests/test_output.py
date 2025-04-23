import pytest
from click.testing import CliRunner
from symbex.cli import cli


@pytest.mark.parametrize(
    "extra_args,expected,expected_error",
    (
        (["--json"], '[{"id": "symbex.py:1", "code": "def blah():"}]\n', None),
        (["--csv"], "id,code\nsymbex.py:1,def blah():\n", None),
        (["--tsv"], "id\tcode\nsymbex.py:1\tdef blah():\n", None),
        (["--nl"], '{"id": "symbex.py:1", "code": "def blah():"}\n', None),
        # ID prefix
        (
            ["--nl", "--id-prefix", "foo:"],
            '{"id": "foo:symbex.py:1", "code": "def blah():"}\n',
            None,
        ),
        # Error states
        (
            ["--json", "--csv"],
            None,
            "Only one of --csv, --tsv, --json, --nl can be used",
        ),
        (
            ["--id-prefix", "foo:"],
            None,
            "--id-prefix can only be used with --csv, --tsv, --json or --nl",
        ),
    ),
)
def test_output(extra_args, expected, expected_error):
    runner = CliRunner()
    with runner.isolated_filesystem():
        open("symbex.py", "w").write("def blah():\n    pass\n")
        result = runner.invoke(
            cli,
            ["blah", "-s"] + extra_args,
            catch_exceptions=False,
        )
    if expected_error:
        assert result.exit_code != 0
        assert expected_error in result.stdout
    else:
        assert result.exit_code == 0
        assert result.output == expected


def test_output_class_with_methods():
    runner = CliRunner()
    with runner.isolated_filesystem():
        open("symbex.py", "w").write(
            "class Foo:\n"
            "    def bar(self):\n"
            "        pass\n"
            "    def baz(self):\n"
            "        pass\n"
        )
        result = runner.invoke(
            cli,
            ["*", "*.*", "--docs", "--imports", "-n"],
            catch_exceptions=False,
        )
    assert result.exit_code == 0
    assert result.output == (
        "# from symbex import Foo\n"
        "class Foo:\n"
        "\n"
        "    def bar(self):\n"
        "\n"
        "    def baz(self):\n"
        "\n"
    )
