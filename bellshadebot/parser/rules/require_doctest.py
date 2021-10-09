from typing import Union

import libcst as cst
import libcst.matchers as m
from fixit import CstContext, CstLintRule
from fixit import InvalidTestCase as Invalid
from fixit import ValidTestCase as Valid

MISSING_DOCTEST: str = [
    "file tersebut tidak memiliki doctest pada fungsi atau kelas"
    + " pastikan gunakan fungsi doctest pada fungsi `{nodename}`"
]

INIT: str = "__init__"


class RequireDoctestRule(CstLintRule):

    VALID = [
        Valid(
            """
            '''
            Module-level doctstring contains doctest
            >>> foo()
            None
            ```
            def foo():
                pass

            class Bar:
                def baz(self):
                    pass

            def bar():
                pass
            """
        ),
        Valid(
            """
            def foo():
                pass

            def bar():
                pass

            # contains a test function
            def test_foo():
                pass

            class Baz:
                def baz(self):
                    pass

            def spam():
                pass
            """
        ),
        Valid(
            """
            def foo():
                pass

            def bar():
                pass

            def test_foo():
                pass

            def test_bar():
                pass

            class Baz:
                def baz(self):
                    pass

            def spam():
                pass
            """
        ),
        Valid(
            """
            def foo():
                pass

            class Baz:
                def baz(self):
                    pass

            def bar():
                pass

            # contains test class
            class TestSpam:
                def test_spam(self):
                    pass

            def egg():
                pass
            """
        ),
        Valid(
            """
            def foo():
                '''
                >>> foo()
                '''
                pass

            class Spam:
                '''
                Class-level docstring contains doctest
                >>> Spam()
                '''
                def foo(self):
                    pass

                def spam(self):
                    pass

            def bar():
                '''
                >>> bar()
                '''
                pass
            """
        ),
        Valid(
            """
            def spam():
                '''
                >>> spam()
                '''
                pass

            class Bar:
                def __init__(self):
                    pass

                def bar(self):
                    '''
                    >>> bar()
                    '''
                    pass
            """
        ),
    ]

    INVALID = [
        Invalid(
            """
            def bar():
                pass
            """
        ),
        Invalid(
            """
            def foo():
                ''''
                >>> foo()
                '''
                pass

            class Spam:
                def __init__(self):
                    pass

                def spam(self):
                    pass
            """
        ),
        Invalid(
            """
            def bar():
                '''
                >>> bar()
                '''
                pass

            class Spam:
                '''
                >>> Spam()
                '''
                def spam():
                    pass

            def egg():
                pass
            """
        ),
    ]

    def __init__(self, context: CstContext) -> None:
        super().__init__(context)
        self._skip_doctest: bool = False
        self._temporary: bool = False

    def visit_Module(self, node: cst.Module) -> None:
        self._skip_doctest = self._has_testnode(node) or self._has_doctest(node)

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        self._temporary = self._skip_doctest
        self._skip_doctest = self._has_doctest(node)

    def leave_ClassDef(self, original_node: cst.ClassDef) -> None:
        self._skip_doctest = self._temporary

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        nodename = node.name.value
        if nodename != INIT and not self._has_doctest(node):
            self.report(
                node,
                MISSING_DOCTEST.format(
                    filepath=self.context.file_path, nodename=nodename
                ),
            )

    def _has_doctest(
        self, node: Union[cst.Module, cst.ClassDef, cst.FunctionDef]
    ) -> bool:
        if not self._skip_doctest:
            docstring = node.get_docstring()
            if docstring is not None:
                for line in docstring.splitlines():
                    if line.strip().startswith(">>> "):
                        return True
            return False
        return True

    @staticmethod
    def _has_testnode(node: cst.Module) -> bool:
        return m.matches(
            node,
            m.Module(
                body=[
                    m.ZeroOrMore(),
                    m.AtLeastN(
                        n=1,
                        matcher=m.OneOf(
                            m.FunctionDef(
                                name=m.Name(
                                    value=m.MatchIfTrue(
                                        lambda value: value.startswith("test_")
                                    )
                                )
                            ),
                            m.ClassDef(
                                name=m.Name(
                                    value=m.MatchIfTrue(
                                        lambda value: value.startswith("Test")
                                    )
                                )
                            ),
                        ),
                    ),
                    m.ZeroOrMore(),
                ]
            ),
        )
