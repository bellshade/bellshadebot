import libcst as cst
import libcst.matchers as m
from fixit import CstLintRule
from fixit import InvalidTestCase as Invalid
from fixit import ValidTestCase as Valid


class UseFstringRule(CstLintRule):
    MESSAGE: str = (
        "[peraturan kontribusi]"
        + "(https://github.com/bellshade/Python/blob/main/CONTRIBUTING.md)"
        + " pastikan tidak menggunakan printf style format ata `str.format()`."
        + "gunakan [f-string](https://realpython.com/apython-f-strings/)"
    )
    VALID = [
        Valid("assigned='string'; f'testing' {assigned}"),
        Valid("'simple string'"),
        Valid("'concatenated' + 'string'"),
        Valid("b'bytes %s' % 'string'.encode('utf-8')"),
    ]

    INVALID = [
        Invalid("'hello, {name}'.format(name='you')"),
        Invalid("'hello, %s' % 'you'"),
        Invalid("r'raw string value=%s' % val"),
    ]

    def visit_Call(self, node: cst.Call) -> None:
        if m.matches(
            node,
            m.Call(
                func=m.Attribute(value=m.SimpleString(), attr=m.Name(value="format"))
            ),
        ):
            self.report(node)

    def visit_BinaryOperation(self, node: cst.BinaryOperation) -> None:
        if m.matches(
            node, m.BinaryOperation(left=m.SimpleString(), operator=m.Modulo())
        ) and isinstance(
            cst.ensure_type(node.left, cst.SimpleString).evaluated_value, str
        ):
            self.report(node)
