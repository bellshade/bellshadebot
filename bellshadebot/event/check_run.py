import logging
from typing import Any

from gidgethub import routing
from gidgethub.sansio import Event

from bellshadebot import utils
from bellshadebot.api import GitHubAPI
from bellshadebot.constant import Label

check_run_router = routing.Router()
logger = logging.getLogger(__package__)


@check_run_router.register("check_run", action="completed")
async def check_ci_status_and_label(
    event: Event, gh: GitHubAPI, *args: Any, **kwargs: Any
) -> None:
    repository = event.data["repository"]["full_name"]

    try:
        commit_sha = event.data["check_run"]["head_sha"]
        pr_for_commit = await utils.get_pr_for_commit(
            gh, sha=commit_sha, repository=repository
        )
    except KeyError:
        commit_sha = event.data["pull_request"]["head"]["sha"]
        pr_for_commit = event.data["pull_request"]

    if pr_for_commit is None:
        logger.info(
            "pull request tidak ditemukan untuk commit : %s",
            f"https://github.com/{repository}/commit/{commit_sha}",
        )
        return None

    check_runs = await utils.get_check_runs_for_commit(
        gh, sha=commit_sha, repository=repository
    )

    all_check_run_status: list[str] = [
        check_run["status"] for check_run in check_runs["check_runs"]
    ]
    all_check_run_conclusion: list[str] = [
        check_run["conclusion"] for check_run in check_runs["check_runs"]
    ]

    if (
        "in_progress" not in all_check_run_status
        and "queued" not in all_check_run_status
    ):
        current_labels: list[str] = [label["name"] for label in pr_for_commit["labels"]]
        if any(
            conclusion in [None, "failure", "timed_out"]
            for conclusion in all_check_run_conclusion
        ):
            if Label.FAILED_TEST not in current_labels:
                await utils.add_label_to_pr_or_issue(
                    gh, label=Label.FAILED_TEST, pr_or_issue=pr_for_commit
                )
        elif Label.FAILED_TEST in current_labels:
            await utils.remove_label_from_pr_or_issue(
                gh, label=Label.FAILED_TEST, pr_or_issue=pr_for_commit
            )
