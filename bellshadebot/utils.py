from __future__ import annotations

import urllib.parse
from base64 import b64decode
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from bellshadebot.api import GitHubAPI
from bellshadebot.constant import PR_REVIEW_BODY


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
async def add_label_to_pr_or_issue(
    gh: GitHubAPI, *, label: Union[str, list[str]], pr_or_issue: Mapping[str, Any]
) -> None:
    labels_url = (
        pr_or_issue["labels_url"]
        if "labels_url" in pr_or_issue
        else pr_or_issue["issue_url"] + "/labels"
    )
    await gh.post(
        labels_url,
        data={"labels": [label] if isinstance(label, str) else label},
        oauth_token=await gh.access_token,
    )


async def remove_label_from_pr_or_issue(
    gh: GitHubAPI,
    *,
    label: Union[str, list[str]],
    pr_or_issue: Mapping[str, Any],
) -> None:
    labels_url = (
        pr_or_issue["labels_url"]
        if "labels_url" in pr_or_issue
        else pr_or_issue["issue_url"] + "/labels"
    )
    label_list = [label] if isinstance(label, str) else label
    for label in label_list:
        parse_label = urllib.parse.quote(label)
        await gh.delete(
            f"{labels_url}/{parse_label}",
            oauth_token=await gh.access_token,
        )


async def get_user_open_pr_numbers(
    gh: GitHubAPI, *, user_login: str, repository: str
) -> list[str]:
    search_url = (
        f"/search/issues?q=type:pr+state:open+repo:{repository}+author:{user_login}"
    )
    pr_numbers = []
    async for pull in gh.getiter(search_url, oauth_token=await gh.access_token):
        pr_numbers.append(pull["number"])
    return pr_numbers


async def add_comment_to_pr_or_issue(
    gh: GitHubAPI, *, comment: str, pr_or_issue: Mapping[str, Any]
) -> None:
    await gh.post(
        pr_or_issue["comments_url"],
        data={"body": comment},
        oauth_token=await gh.access_token,
    )


async def close_pr_or_issue(
    gh: GitHubAPI,
    *,
    comment: str,
    pr_or_issue: Mapping[str, Any],
    label: Optional[Union[str, list[str]]] = None,
) -> None:
    await add_comment_to_pr_or_issue(gh, comment=comment, pr_or_issue=pr_or_issue)
    if label is not None:
        await add_label_to_pr_or_issue(gh, label=label, pr_or_issue=pr_or_issue)
    await gh.patch(
        pr_or_issue["url"],
        data={"state": "closed"},
        oauth_token=await gh.access_token,
    )
    try:
        if pr_or_issue["requested_reviewers"]:
            await remove_requested_reviewers_from_pr(gh, pull_request=pr_or_issue)
    except KeyError:
        pass


async def remove_requested_reviewers_from_pr(
    gh: GitHubAPI, *, pull_request: Mapping[str, Any]
) -> None:
    await gh.delete(
        pull_request["url"] + "/requested_reviewers",
        data={
            "reviewers": [
                reviewer["login"] for reviewer in pull_request["requested_reviewers"]
            ]
        },
        oauth_token=await gh.access_token,
    )


async def get_pr_files(gh: GitHubAPI, *, pull_request: Mapping[str, Any]) -> list[File]:
    files = []
    async for data in gh.getiter(
        pull_request["url"] + "/files", oauth_token=await gh.access_token
    ):
        files.append(
            File(
                data["filename"],
                Path(data["filename"]),
                data["contents_url"],
                data["status"],
            )
        )
    return files


async def get_file_content(gh: GitHubAPI, *, file: File) -> bytes:
    data = await gh.getitem(
        file.contents_url,
        oauth_token=await gh.access_token,
    )
    return b64decode(data["content"])


async def create_pr_review(
    gh: GitHubAPI, *, pull_request: Mapping[str, Any], comments: list[dict[str, Any]]
) -> None:
    await gh.post(
        pull_request["url"] + "/reviews",
        data={
            "commit_id": pull_request["head"]["sha"],
            "body": PR_REVIEW_BODY,
            "event": "COMMENT",
            "comments": comments,
        },
        accept="application/vnd.github.comfort-fade-preview+json",
        oauth_token=await gh.access_token,
    )


async def add_reaction(
    gh: GitHubAPI, *, reaction: str, comment: Mapping[str, Any]
) -> None:
    await gh.post(
        comment["url"] + f"/reactions",
        data={"content": reaction},
        accept="application/vnd.github.squirrel-girl-preview+json",
        oauth_token=await gh.access_token,
    )


async def get_pr_for_issue(gh: GitHubAPI, *, issue: Mapping[str, Any]) -> Any:
    return await gh.getitem(
        issue["pull_request"]["url"], oauth_token=await gh.access_token
    )


async def update_pr(gh: GitHubAPI, *, pull_request: Mapping[str, Any]) -> Any:
    return await gh.getitem(pull_request["url"], oauth_token=await gh.access_token)
