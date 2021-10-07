from __future__ import annotations

import traceback
from dataclasses import asdict, dataclass, field
from typing import Any, Collection, Union

from fixit.common.report import BaseLintRuleReport
from libcst import ParserSyntaxError
from libcst._nodes.expression import BaseAssignTargetExpression
from libcst._nodes.whitespace import Comment

from bellshadebot.constant import Label

RULE_TO_LABEL: dict[str, str] = {
    "RequeireDescriptiveNameRule": Label.DESCRIPTIVE_NAME,
    "RequireDoctestRule": Label.REQUIRE_TEST,
    "RequireTypeHintRule": Label.TYPE_HINT,
}
MULTIPLE_COMMENT_SEPARATOR: str = "\n\n"


@dataclass(frozen=False)
class ReviewComment:
    body: str
    path: str
    line: str
    side: str = field(init=False, default="RIGHT")


@dataclass
class PUllRequestReviewRecord:
    labels_to_add: list[str] = field(default_factory=list, init=False)
    labels_to_remove: list[str] = field(default_factory=list, init=False)

    _comments: list[ReviewComment] = field(default_factory=list, init=False, repr=False)
    _violated_ruoles: set[str] = field(default_factory=set, init=False, repr=False)

    def add_comments(
        self, reports: Collection[BaseAssignTargetExpression], filepath: str
    ) -> None:
        for report in reports:
            self._violated_ruoles.add(report.code)
            if self._lineno_exist(report.message, filepath, report.line):
                continue
            self._comments.append(ReviewComment(report.message, filepath, report.line))

    def add_error(
        self, exc: Union[SyntaxError, ParserSyntaxError], filepath: str
    ) -> None:
        message = traceback.format_exc(limit=1)
        if isinstance(exc, SyntaxError):
            lineno = exc.lineno or 1
        else:
            lineno = exc.raw_line

        body = f"error ketika parsing file: `{filepath}`\n" f"```python\n{message}\n```"
        self._comments.append(ReviewComment(body, filepath, lineno))

    def fill_labels(self, current_labels: Collection[str]) -> None:
        for rule, label in RULE_TO_LABEL.items():
            if rule in self._violated_ruoles:
                if label not in current_labels and label not in self.labels_to_add:
                    self.labels_to_add.append(label)

            elif label in current_labels and label not in self.labels_to_remove:
                self.labels_to_remove.append(label)

    def collect_comments(self) -> list[dict[str, Any]]:
        return [asdict(comment) for comment in self._comments]

    def collect_review_contents(self) -> list[str]:
        content = []
        for comment in self._comments:
            if MULTIPLE_COMMENT_SEPARATOR in comment.body:
                comment.body = comment.body.replace(
                    MULTIPLE_COMMENT_SEPARATOR,
                    f"{MULTIPLE_COMMENT_SEPARATOR}**{comment.path}:{comment.line}**",
                )
            content.append(f"**{comment.path}:{comment.line}:** {comment.body}")

        return content

    def _lineno_exist(self, body: str, filepath: str, lineno: int) -> bool:
        for comment in self._comments:
            if comment.line == lineno and comment.path == filepath:
                comment.body += f"{MULTIPLE_COMMENT_SEPARATOR}{body}"
                return True
        return False
