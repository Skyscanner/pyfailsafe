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
from failsafe import Failsafe, RetryPolicy, CircuitBreaker, FailsafeError


class GitHubClientError(Exception):
    pass


class GitHubClient:
    def __init__(self):
        self.failsafe = Failsafe(retry_policy=RetryPolicy(allowed_retries=4),
                                 circuit_breaker=CircuitBreaker(maximum_failures=8))

    async def get_repositories_by_user(self, github_user):
        url = 'https://api.github.com/orgs/{}/repos'.format(github_user)

        try:
            return await self.failsafe.run(lambda: self._request(url))
        except FailsafeError as e:
            raise GitHubClientError("Could not load repositories") from e

    async def _request(self, url):
        with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception()  # exception raised tells Failsafe to retry
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
