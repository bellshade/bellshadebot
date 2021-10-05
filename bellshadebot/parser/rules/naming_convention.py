from enum import Enum
from typing import Collection, Optional
import libcst as cst
import libcst.matchers as m
from fixit import CstContext, CstLintRule
from fixit import InvalidTestCase as Invalid
from fixit import ValidTestCase as Valid
from libcst.metadata import QualifiedName, QualifiedNameProvider

INVALID_CAMEL_CASE_NAME_COMMENT: str = (
    "nama kelas harus menggunakan [``CamelCase``]"
    + "(https://en.wikipedia.org/wiki/Camel_case)"
)

INVALID_SNAKE_CASE_NAME_COMMENT: str = (
    "nama variabel dan fungsi harus menggunakan [``snake_case``]"
    + "(https://en.wikipedia.org/wiki/Snake_case)"
)


class NamingConvention(Enum):
    CAMEL_CASE = INVALID_CAMEL_CASE_NAME_COMMENT
    SNAKE_CASE = INVALID_SNAKE_CASE_NAME_COMMENT

    def valid(self, name: str) -> bool:
        if self is NamingConvention.CAMEL_CASE:
            name = name.strip("_")
            if name[0].islower() or "_" in name:
                return False

        else:
            if name.lower() != name and name.upper() != name:
                return False
        
        return True

class NamingConventionRule(CstLintRule):

    METADATA_DEPENDENCIES = (QualifiedNameProvider, )  # type: ignore
    
    VALID = [
        Valid("type_hint: str"),
        Valid("type_hint_var: int = 5"),
        Valid("CONSTANT_WITH_UNDERSCORE12 = 10"),
        Valid("hello = 'world'"),
        Valid("snake_case = 'assign'"),
        Valid("for iteration in range(5): pass"),
        Valid("class _PrivateClass: pass"),
        Valid("class SomeClass: pass"),
        Valid("class One: pass"),
        Valid("def oneword(): pass"),
        Valid("def some_extra_words(): pass"),
        Valid("all = names_are = valid_in_multiple_assign = 5"),
        Valid("(walrus := 'operator')"),
        Valid("multiple, valid, assingments = 1, 2, 3"),
        Valid(
            """
            class Spam:
                def __init__(self, valid, another_valid):
                    self.valid = valid,
                    self.another_valid = another_valid
                    self._private = None
                    self._private = None
                    self._extreme_private = None
                
                def bar(self):
                    # testing
                    return self.some_Invalid_NaMe
            """
        ),
        
    ]