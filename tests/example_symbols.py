from typing import Tuple


# Function with no arguments
def func_no_args():
    "This has a single line docstring"
    pass


# Function with positional arguments
def func_positional_args(a, b, c):
    """This has a
    multi-line docstring"""
    pass


# Async function
async def async_func(a, b, c):
    pass


# Function with default arguments
def func_default_args(a, b=2, c=3):
    pass


# Function with arbitrary number of positional arguments
def func_arbitrary_positional_args(*args):
    pass


# Function with arbitrary number of keyword arguments
def func_arbitrary_keyword_args(**kwargs):
    pass


# Function with both arbitrary positional and keyword arguments
def func_arbitrary_args(*args, **kwargs):
    pass


# Function with positional-only arguments (Python 3.8 and above)
def func_positional_only_args(a, /, b, c):
    pass


# Function with keyword-only arguments
def func_keyword_only_args(a, *, b, c):
    pass


# Function with type annotations (Python 3.5 and above)
def func_type_annotations(a: int, b: str) -> bool:
    pass


# Class with no base classes
class ClassNoBase:
    pass


# Class with a single base class
class ClassSingleBase(int):
    pass


# Class with multiple base classes
class ClassMultipleBase(int, str):
    pass


# Class with a metaclass
class ClassWithMeta(metaclass=type):
    pass


# Class with methods
class ClassWithMethods:
    def __init__(self, a):
        pass

    def method_types(self, b: int) -> bool:
        return True

    def method_positional_only_args(a, /, b, c):
        pass

    def method_keyword_only_args(a, *, b, c):
        pass

    async def async_method(a, b, c):
        pass


# Borrowed from Jedi
# https://github.com/simonw/symbex/issues/16
def function_with_non_pep_0484_annotation(
    x: "I can put anything here",
    xx: "",
    yy: "\r\n\0;+*&^564835(---^&*34",
    y: 3 + 3,
    zz: float,
) -> int("42"):
    pass


def complex_annotations(
    code: str, symbols: Iterable[str]
) -> List[Tuple[AST, Optional[str]]]:
    pass


# For testing --typed/--untyped/etc


def func_fully_typed(a: int, b: str) -> bool:
    pass


async def async_func_fully_typed(a: int, b: str) -> bool:
    pass


def func_partially_typed(a: int, b) -> bool:
    pass


def func_partially_typed_no_typed_return(a: int, b: int):
    pass


def func_partially_typed_only_typed_return(a, b) -> int:
    pass


def func_typed_no_params() -> None:
    pass


def _private() -> None:
    pass


class ClassForTypedTests:
    def __init__(self, a: int):
        pass

    def method_fully_typed(self, a: int, b: str) -> bool:
        "Single line"
        pass

    def method_partially_typed(self, a: int, b) -> bool:
        """Multiple
        lines"""
        pass

    def method_untyped(self, a, b):
        pass

    def _private_method(self):
        pass


class _PrivateClass:
    pass
