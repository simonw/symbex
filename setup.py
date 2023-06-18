from setuptools import setup
import os

VERSION = "0.2"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="pyseek",
    description="Find the Python code for specified symbols",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/pyseek",
    project_urls={
        "Issues": "https://github.com/simonw/pyseek/issues",
        "CI": "https://github.com/simonw/pyseek/actions",
        "Changelog": "https://github.com/simonw/pyseek/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["pyseek"],
    entry_points="""
        [console_scripts]
        pyseek=pyseek.cli:cli
    """,
    install_requires=["click"],
    extras_require={"test": ["pytest", "pytest-icdiff"]},
    python_requires=">=3.8",
)
