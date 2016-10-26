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

import asyncio
import pytest

loop = asyncio.get_event_loop()


def test_simple_failsafe_should_return_when_user_exists():
    from examples.simple_failsafe import GitHubClient

    github_client = GitHubClient()

    result = loop.run_until_complete(
        github_client.get_repositories_by_user('skyscanner')
    )

    assert result is not None


def test_simple_failsafe_should_raise_when_user_not_exists():
    from examples.simple_failsafe import GitHubClient, UserNotFoundError

    github_client = GitHubClient()

    with pytest.raises(UserNotFoundError):
        loop.run_until_complete(
            github_client.get_repositories_by_user('not-existing-user')
        )


def test_failsafe_with_fallback():
    from examples.failsafe_with_fallback import GitHubClient

    github_client = GitHubClient()
    result = loop.run_until_complete(
        github_client.get_repositories_by_user('skyscanner')
    )

    assert result is not None


def test_fallback_failsafe():
    from examples.fallback_failsafe import GitHubClient

    github_client = GitHubClient()
    result = loop.run_until_complete(
        github_client.get_repositories_by_user('skyscanner')
    )

    assert result is not None
