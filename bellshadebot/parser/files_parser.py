from __future__ import annotations

import logging
from typing import Any, Collection, Iterable, Mapping

from bellshadebot.constant import Label
from bellshadebot.utils import File

IGNORE_FILES_FOR_TYPELABEL: set[str] = {"directory.md"}
logger = logging.getLogger(__package__)


class BaseFilesParser:
    pr_labels: list[str]
    pr_html_url: str
    DOCS_EXTENSION: Collection[str] = ()
    ACCEPTED_EXTENSION: Collection[str] = ()

    def __init__(
        self, pr_files: Iterable[File], pull_request: Mapping[str, Any]
    ) -> None:
        self.pr = pull_request
        self.pr_files = pr_files
        self.pr_labels = [label["name"] for label in pull_request["labels"]]
        self.pr_html_url = pull_request["html_url"]

    def validate_extension(self) -> str:
        invalid_filepath = []
        for file in self.pr_files:
            filepath = file.path
            if not filepath.suffix:
                if ".github" not in filepath.parts:
                    if filepath.parent.name:
                        invalid_filepath.append(file.name)
                    elif not filepath.name.startswith("."):
                        invalid_filepath.append(file.name)

            elif filepath.suffix not in self.ACCEPTED_EXTENSION:
                invalid_filepath.append(file.name)
        invalid_files = ", ".join(invalid_filepath)
        if invalid_files:
            logger.info("invalid file(s) [%s]: %s", invalid_files, self.pr_html_url)

        return invalid_files

    def type_label(self) -> str:
        label = ""
        for file in self.pr_files:
            if file.path.suffix in self.DOCS_EXTENSION:
                if file.path.name not in IGNORE_FILES_FOR_TYPELABEL:
                    label = Label.DOCUMENTATION
                    break
            elif file.status != "added":
                label = Label.ENHANCEMENT

        return label if label not in self.pr_labels else ""
