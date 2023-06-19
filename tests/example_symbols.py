from typing import Union, Tuple


# Function with no arguments
def func_no_args():
    pass


# Function with positional arguments
def func_positional_args(a, b, c):
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
