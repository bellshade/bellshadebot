from __future__ import annotations

import importlib
import inspect
import logging
from typing import Any, Iterable, Iterator, Mapping

from fixit import CstLintRule, LintConfig
from fixit.common.utils import LintRuleCollectionT
from fixit.rule_lint_engine import lint_file
from libcst import ParserSyntaxError

from bellshadebot.parser.files_parser import BaseFilesParser
from bellshadebot.parser.record import PullRequestReviewRecord
from bellshadebot.parser.rules import RequireDoctestRule
from bellshadebot.utils import File

RULES_DOTPATH: str = "bellshadebot.parser.rules"

DEFAULT_CONFIG: LintConfig = LintConfig(packages=[RULES_DOTPATH])
logger = logging.get_logger(__package__)


def get_rules_from_config(config: LintConfig = DEFAULT_CONFIG) -> LintRuleCollectionT:
    rules: LintRuleCollectionT = set()
    block_list_rules = config.block.list_rules
    for package in config.packages:
        pkg = importlib.import_module(package)
        for name in dir(pkg):
            if name.endswith("Rule"):
                obj = getattr(pkg, name)
                if (
                    obj is not CstLintRule
                    and issubclass(obj, CstLintRule)
                    and not inspect.isabstract(obj)
                    and name not in block_list_rules
                ):
                    rules.add(obj)

    return rules


class PythonParser(BaseFilesParser):
    _pr_report: PullRequestReviewRecord
    _rules: LintRuleCollectionT

    DOCS_EXTENSION: tuple[str, ...] = (".md", ".rst")

    ACCEPTED_EXTENSION: tuple[str, ...] = (
        ".ini",
        ".toml",
        ".yaml",
        ".cfg",
        ".csv",
        ".json",
        ".txt",
        ".py",
    ) + DOCS_EXTENSION

    def __init__(
        self,
        pr_files: Iterable[File],
        pull_request: Mapping[str, Any],
    ) -> None:
        super().__init__(pr_files, pull_request)
        self._pr_record = PullRequestReviewRecord()
        self._rules = get_rules_from_config()
        if self._contains_testfile():
            self._rules.discard(RequireDoctestRule)

    property

    def labels_to_add(self) -> list[str]:
        return self._pr_record.labels_to_add

    @property
    def labels_to_remove(self) -> list[str]:
        return self._pr_record.labels_to_remove

    def collect_comments(self) -> list[dict[str, Any]]:
        return self._pr_record.collect_comments()

    def collect_review_contents(self) -> list[str]:
        return self._pr_record.collect_review_contents()

    def files_to_check(self, ignore_modified: bool) -> Iterator[File]:
        for file in self.pr_files:
            filepath = file.path
            if (
                (not ignore_modified or file.status == "added")
                and filepath.suffix == ".py"
                and "scripts" not in filepath.parts
                and not filepath.name.startswith("__")
                and (
                    not (
                        filepath.name.startswith("test_")
                        or filepath.name.endswith("_test.py")
                    )
                )
            ):
                yield file

        self._pr_record.fill_labels(self.pr_labels)

    def parse(self, file: File, source: bytes) -> None:
        try:
            reports = lint_file(
                file.path,
                source,
                use_ignore_byte_markers=False,
                use_ignore_comments=False,
                config=DEFAULT_CONFIG,
                rules=self._rules,
            )
            self._pr_record.add_comments(reports, file.name)
        except (SyntaxError, ParserSyntaxError) as exc:
            self._pr_record.add_error(exc, file.name)
            logger.info(
                "invalid kode python pada file: [%s] %s", file.name, self.pr_html_url
            )

    def _contains_testfile(self) -> bool:
        for file in self.pr_files:
            filepath = file.path
            if filepath.suffix == ".py" and (
                filepath.name.startswith("test_") or filepath.name.endswith("_test.py")
            ):
                return True

        return False
