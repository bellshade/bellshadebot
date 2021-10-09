from gidgethub.routing import Router

from bellshadebot.event.check_run import check_run_router
from bellshadebot.event.commands import commands_router
from bellshadebot.event.installation import installation_router
from bellshadebot.event.issues import issues_router
from bellshadebot.event.pull_request import pull_request_router

main_router: Router = Router(
    check_run_router,
    commands_router,
    installation_router,
    issues_router,
    pull_request_router,
)

__all__ = ["main_router"]
