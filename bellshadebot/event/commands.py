import logging
import re
from typing import Any, Pattern

from gidgethub import routing
from gidgethub.sansio import Event

from bellshadebot import utils
from bellshadebot.api import GitHubAPI
from bellshadebot.event.pull_request import check_pr_files

commands_router = routing.Router()

COMMAND_RE: Pattern[str] = re.compile(
    r"@bellshadebot\s+([a-z\-]+)",
    re.IGNORECASE,
)

logger = logging.getLogger(__package__)


@commands_router.register("issue_comment", action="created")
async def main(
    event: Event,
    gh: GitHubAPI,
    *args: any,
    **kwargs: Any,
) -> None:
    comment = event.data["comment"]
    if comment["author_association"].lower() not in {"member", "owner"}:
        return None

    if match := COMMAND_RE.search(comment["body"]):
        command = match.group(1).lower()
        logger.info("match=%s command=%s", match.string, command)
        if command == "reviewer":
            await review(event, gh, *args, **kwargs)
        elif command == "review-all":
            await review(event, gh, *args, ingored_modified=False, **kwargs)


async def review(event: Event, gh: GitHubAPI, *args: Any, **kwargs: Any) -> None:
    issue = event.data["issue"]
    comment = event.data["comment"]

    if "pull_request" in issue:
        await utils.add_reaction(gh, reaction="+1", comment=comment)
        event.data["pull_requet"] = await utils.get_pr_for_issue(gh, issue=issue)
        await check_pr_files(event, gh, *args, **kwargs)
    else:
        await utils.add_reaction(gh, reaction="-1", comment=comment)
