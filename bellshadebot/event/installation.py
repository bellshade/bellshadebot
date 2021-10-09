import logging
from typing import Any

from gidgethub import routing
from gidgethub.sansio import Event

from bellshadebot.api import GitHubAPI
from bellshadebot.constant import GRETTING_COMMENT

installation_router = routing.Router()
logger = logging.getLogger(__package__)


@installation_router.register("installation", action="created")
@installation_router.register("installation_repositories", action="added")
async def repo_installation_added(
    event: Event, gh: GitHubAPI, *args: Any, **kwargs: Any
) -> None:
    try:
        repositories = event.data["repositories"]
    except KeyError:
        repositories = event.data["repositories_added"]

    for repository in repositories:
        repo_name = repository["full_name"]
        logger.info("repositori baru telah dibuat : %s", repo_name)
        response = await gh.post(
            f"/repos/{repo_name}/issues",
            data={
                "title": "install sukses",
                "body": GRETTING_COMMENT.format(login=event.data["sender"]["login"]),
            },
            oauth_token=await gh.access_token,
        )
        issue_url = response["url"]
        await gh.patch(
            issue_url,
            data={"state": "closed"},
            oauth_token=await gh.access_token,
        )
