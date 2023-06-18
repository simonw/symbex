from setuptools import setup
import os

VERSION = "0.4.1"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="py-grep",
    description="Find the Python code for specified symbols",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/py-grep",
    project_urls={
        "Issues": "https://github.com/simonw/py-grep/issues",
        "CI": "https://github.com/simonw/py-grep/actions",
        "Changelog": "https://github.com/simonw/py-grep/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["py_grep"],
    entry_points="""
        [console_scripts]
        py-grep=py_grep.cli:cli
    """,
    install_requires=["click"],
    extras_require={"test": ["pytest", "pytest-icdiff"]},
    python_requires=">=3.7",
)
