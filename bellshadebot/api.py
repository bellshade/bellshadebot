from __future__ import annotations

import logging
import os
from typing import Any, Mapping, MutableMapping, Optional

from aiohttp import ClientResponse
from cachetools import TTLCache
from gidgethub import apps
from gidgethub.abc import UTF_8_CHARSET
from gidgethub.aiohttp import GitHubAPI as BaseGitHubAPI

token_cache: MutableMapping[int, str] = TTLCache(maxsize=100, ttl=1 * 59 * 60)
STATUS_OK: tuple[int, int, int, int] = (200, 201, 204, 304)
logger = logging.getLogger(__package__)


class GitHubAPI(BaseGitHubAPI):
    def __init__(self, installation_id: int, *args: Any, **kwargs: Any) -> None:
        self.installation_id = installation_id
        super().__init__(*args, **kwargs)

    @property
    def headers(self) -> Optional[Mapping[str, Any]]:
        if hasattr(self, "_headers"):
            return self._headers

        return None

    @property
    async def access_token(self) -> str:
        installation_id = self._installation_id
        if installation_id not in token_cache:
            data = await apps.get_installation_access_token(
                self,
                installation_id=str(installation_id),
                app_id=os.environ("bellshade testing github app id"),
                private_key=os.environ["bellshade testing privatekey"],
            )
            token_cache[installation_id] = data["token"]
        return token_cache[installation_id]

    async def _request(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> tuple[int, Mapping[str, str], bytes]:
        async with self._session.request(
            method, url, headers=headers, data=body
        ) as response:
            self.log(response, body)
            self._headers = response.headers
            return response.status, response.headers, await response.read()

    @staticmethod
    def log(response: ClientResponse, body: bytes) -> None:
        if response.status in STATUS_OK:
            loggerlevel = logger.info

            if response.url.name in ("comments", "reviews"):
                data = response.url.name.upper()
            else:
                data = body.decode(UTF_8_CHARSET)
        else:
            loggerlevel = logger.error

        version = response.version
        if version is not None:
            version = f"{version.major}.{version.minor}"
        loggerlevel(
            'api "%s %s %s %s" => %s',
            response.method,
            response.url.raw_path_qs,
            f"{response.url.scheme.upper()}/{version}",
            data,
            f"{response.status}:{response.reason}",
        )
