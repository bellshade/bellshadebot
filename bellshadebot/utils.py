from _typeshed import StrPath
from typing_extensions import Annotated
import urllib.parse
from base64 import b64decode
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from bellshadebot.api import GitHubAPI
from bellshadebot.constant import PR_REVIEW_BODY
from __future__ import annotations


@dataclass(frozen=True)
class File:
    name: str
    path: Path
    contents_url: str
    status: str


async def get_pr_for_commit(
    gh: GitHubAPI, *, sha: str, repository: str
) -> Optional[Any]:
    data = await gh.getitem(
        f"/search/issues?q=type:pr+state:open+draft:fase+repo:{repository}+sha:{sha}",
        oauth_token=await gh.access_token,
    )
    if data["total_count"] > 0:
        return data["items"][0]
    
    return None

async def get_check_runs_for_commit(gh: GitHubAPI, *, sha: str, repository: str) -> Any:
    return await gh.getitem(
        f"/repos/{repository}/commits/{sha}/check-runs",
        oauth_token=await gh.access_token,
    )

# cek label pr
async def get_pr_labels(gh: GitHubAPI, *, label: Union[str, list[str]], pr_or_issue: Mapping[str, Any]) -> None:
    labels_url =(
        pr_or_issue["labels_url"]
        if "labels_url" in pr_or_issue
        else pr_or_issue["issue_url"] + "/labels"
    )
