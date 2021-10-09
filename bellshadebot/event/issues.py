import logging
from abc import abstractmethod
from typing import Any

from gidgethub import routing
from gidgethub.sansio import Event

from bellshadebot import utils
from bellshadebot.api import GitHubAPI
from bellshadebot.constant import EMPTY_PR_BODY_COMMENT, Label

issues_router = routing.Router()

logger = logging.getLogger(__package__)


@issues_router.register("issues", action="opened")
async def close_invalid_issue(
    event: Event, gh: GitHubAPI, *args: Any, **kwargs: Any
) -> None:
    issue = event.data["issue"]
    if not issue["body"]:
        logger.info("issue kosong: %s", issue["html_url"])
        await utils.close_pr_or_issue(
            gh,
            comment=EMPTY_PR_BODY_COMMENT.format(user_login=issue["user"]["login"]),
            pr_or_issue=issue,
            label=Label.INVALID,
        )
