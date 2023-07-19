from setuptools import setup
import os

VERSION = "1.3"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="symbex",
    description="Find the Python code for specified symbols",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/symbex",
    project_urls={
        "Issues": "https://github.com/simonw/symbex/issues",
        "CI": "https://github.com/simonw/symbex/actions",
        "Changelog": "https://github.com/simonw/symbex/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["symbex"],
    entry_points="""
        [console_scripts]
        symbex=symbex.cli:cli
    """,
    install_requires=["click"],
    extras_require={"test": ["pytest", "pytest-icdiff", "cogapp", "PyYAML", "ruff"]},
    python_requires=">=3.8",
)
