# Copyright 2016 Skyscanner Limited.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import aiohttp
from urllib.parse import urljoin

from failsafe import FallbackFailsafe


class GitHubClient:
    def __init__(self):
        # primary endpoint intentionally wrong to simulate failure
        primary_endpoint = 'https://wrong_url.github.com'
        fallback_endpoint = 'https://api.github.com'

        self.fallback_failsafe = FallbackFailsafe([primary_endpoint, fallback_endpoint])

    async def get_repositories_by_user(self, github_user):
        query_path = '/orgs/{}/repos'.format(github_user)

        return await self.fallback_failsafe.run(self._request, query_path)

    async def _request(self, endpoint, query_path):
        url = urljoin(endpoint, query_path)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception()
                return await resp.json()


if __name__ == "__main__":

    async def print_response():
        from pprint import pprint

        github_client = GitHubClient()
        repositories = await github_client.get_repositories_by_user('skyscanner')

        pprint(repositories[0])

    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(print_response())
    loop.close()
