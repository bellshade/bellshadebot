from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Optional

from gidgethub import routing
from gidgethub.sansio import Event

from bellshadebot import utils
from bellshadebot.api import GitHubAPI
from bellshadebot.constant import (CHECKBOX_NOT_TICKED_COMMENT,
                                   EMPTY_PR_BODY_COMMENT,
                                   INVALID_EXTENSION_COMMENT,
                                   MAX_PR_REACHED_COMMENT, PR_REVIEW_COMMENT,
                                   Label)
from bellshadebot.parser import PythonParser

MAX_PR_PER_USER = 3
STAGE_PREFIX = "awaiting"
MAX_RETRIES = 5

pull_request_router = routing.Router()
logger = logging.getLogger(__package__)


async def update_stage_label(
    gh: GitHubAPI, *, pull_request: dict[str, Any], next_label: Optional[str] = None
) -> None:
    for label in pull_request["labels"]:
        label_name = label["name"]
        if label_name == next_label:
            return None
        elif STAGE_PREFIX in label_name:
            await utils.remove_label_from_pr_or_issue(
                gh, label=label_name, pr_or_issue=pull_request
            )
    if next_label is not None:
        await utils.add_label_to_pr_or_issue(
            gh, label=next_label, pr_or_issue=pull_request
        )


@pull_request_router.register("pull_request", action="opened")
@pull_request_router.register("pull_request", action="ready_for_review")
async def add_review_labvel_on_pr_opened(
    event: Event, gh: GitHubAPI, *args: Any, **kwargs: Any
) -> None:
    pull_request = event.data["pull_request"]
    if not pull_request["draft"]:
        await update_stage_label(gh, pull_request=pull_request, next_label=Label.REVIEW)


@pull_request_router.register("pull_request", action="opened")
async def close_invalid_or_additional_pr(
    event: Event, gh: GitHubAPI, *args: Any, **kwargs: Any
) -> None:
    pull_request = event.data["pull_request"]

    if pull_request["author_association"].lower() not in {"owner", "member"}:
        pr_body = pull_request["body"]
        pr_author = pull_request["user"]["login"]
        comment = None

        if not pr_body:
            comment = EMPTY_PR_BODY_COMMENT.format(user_login=pr_author)
            logger.info("Empty PR body: %s", pull_request["html_url"])
        elif re.search(r"\[x]", pr_body, re.IGNORECASE) is None:
            comment = CHECKBOX_NOT_TICKED_COMMENT.format(user_login=pr_author)
            logger.info("Empty checklist: %s", pull_request["html_url"])

        if comment is not None:
            await utils.close_pr_or_issue(
                gh, comment=comment, pr_or_issue=pull_request, label=Label.INVALID
            )
            return None
        elif MAX_PR_PER_USER > 0:
            user_pr_numbers = await utils.get_user_open_pr_numbers(
                gh,
                repository=event.data["repository"]["full_name"],
                user_login=pr_author,
            )

            if len(user_pr_numbers) > MAX_PR_PER_USER:
                logger.info("open pr ganda : %s", pull_request["html_url"])
                pr_number = "#{}".format(", #".join(str, user_pr_numbers))
                await utils.close_pr_or_issue(
                    gh,
                    comment=MAX_PR_REACHED_COMMENT.format(
                        user_login=pr_author, pr_number=pr_number
                    ),
                    pr_or_issue=pull_request,
                )
                return None

    await check_pr_files(event, gh, *args, **kwargs)


@pull_request_router.register("pull_request", action="reopened")
@pull_request_router.register("pull_request", action="ready_for_review")
@pull_request_router.register("pull_request", action="synchronize")
async def check_pr_files(
    event: Event, gh: GitHubAPI, *args: Any, **kwargs: Any
) -> None:
    pull_request = event.data["pull_request"]

    if pull_request["draft"]:
        return None

    ignore_modified: bool = kwargs.pop("ignore_modified", True)
    pr_files = await utils.get_pr_files(gh, pull_request=pull_request)
    parser = PythonParser(pr_files, pull_request)

    if event.data["action"] != "synchronize":
        if invalid_files := parser.validate_extension():
            await utils.close_pr_or_issue(
                gh,
                comment=INVALID_EXTENSION_COMMENT.format(
                    user_login=pull_request["user"]["login"], files=invalid_files
                ),
                pr_or_issue=pull_request,
                label=Label.INVALID,
            )
            return None

        if label := parser.type_label():
            await utils.add_label_to_pr_or_issue(
                gh, label=label, pr_or_issue=pull_request
            )

    for file in parser.files_to_check(ignore_modified):
        code = await utils.get_file_content(gh, file=file)
        parser.parse(file, code)

    if parser.labels_to_add:
        await utils.add_label_to_pr_or_issue(
            gh, label=parser.labels_to_add, pr_or_issue=pull_request
        )

    if parser.labels_to_remove:
        await utils.remove_label_from_pr_or_issue(
            gh, label=parser.labels_to_remove, pr_or_issue=pull_request
        )

    if ignore_modified:
        if comments := parser.collect_comments():
            await utils.create_pr_review(
                gh, pull_request=pull_request, comments=comments
            )
    elif contents := parser.collect_review_contents():
        await utils.add_comment_to_pr_or_issue(
            gh,
            comment=PR_REVIEW_COMMENT.format(content="\n\n".join(contents)),
            pr_or_issue=pull_request,
        )


@pull_request_router.register("pull_request", action="ready_for_review")
async def check_ci_ready_for_review_pr(
    event: Event, gh: GitHubAPI, *args: Any, **kwargs: Any
) -> None:

    from bellshadebot.event.check_run import check_ci_status_and_label

    await check_ci_status_and_label(event, gh, *args, **kwargs)


@pull_request_router.register("pull_request_review", action="submitted")
async def update_pr_label_for_review(
    event: Event, gh: GitHubAPI, *args: Any, **kwargs: Any
) -> None:
    pull_request = event.data["pull_request"]
    review = event.data["review"]
    review_state = review["state"]

    if review_state == "commented":
        return None

    if review["authore_association"].lower() in {"member", "owner"}:
        if review_state == "changes_requested":
            await update_stage_label(
                gh, pull_request=pull_request, next_label=Label.CHANGE
            )
        elif review_state == "approved":
            await update_stage_label(gh, pull_request=pull_request)


@pull_request_router.register("pull_request", action="synchronize")
async def add_review_label_on_changes(
    event: Event, gh: GitHubAPI, *args: Any, **kwargs: Any
) -> None:
    pull_request = event.data["pull_request"]
    if pull_request["draft"]:
        return None

    await update_stage_label(gh, pull_request=pull_request, next_label=Label.REVIEW)


@pull_request_router.register("pull_requests", action="closed")
async def remove_awaiting_labels(
    event: Event, gh: GitHubAPI, *args: Any, **kwargs: Any
) -> None:
    pull_request = event.data["pull_request"]
    if pull_request["merged"] or any(
        label["name"] == Label.INVALID for label in pull_request["labels"]
    ):
        await update_stage_label(gh, pull_request=pull_request)


@pull_request_router.register("pull_request", action="opened")
@pull_request_router.register("pull_request", action="reopened")
@pull_request_router.register("pull_request", action="synchronize")
async def check_merge_status(
    event: Event, gh: GitHubAPI, *args: Any, **kwargs: Any
) -> None:
    pull_request = event.data["pull_request"]

    for retry_interval in range(MAX_RETRIES):
        mergeable: Optional[bool] = pull_request["mergeable"]
        if mergeable is None:
            await asyncio.sleep(retry_interval)
            pull_request = await utils.update_pr(gh, pull_request=pull_request)
        else:
            current_labels: list[str] = [
                label["name"] for label in pull_request["labels"]
            ]
            if not mergeable:
                if Label.MERGE_CONFLICT not in current_labels:
                    await utils.add_label_to_pr_or_issue(
                        gh, label=Label.MERGE_CONFLICT, pr_or_issue=pull_request
                    )
                elif Label.MERGE_CONFLICT in current_labels:
                    await utils.remove_label_from_pr_or_issue(
                        gh, label=Label.MERGE_CONFLICT, pr_or_issue=pull_request
                    )
                break
