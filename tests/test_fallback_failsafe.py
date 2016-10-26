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
import unittest
import pytest

from failsafe import FallbackFailsafe, FallbacksExhausted
from failsafe import RetryPolicy

loop = asyncio.get_event_loop()


class TestFallbackFailsafe(unittest.TestCase):
    def test_value_is_called(self):
        async def call(option):
            assert option == "fallback option 1"
            return "return value"

        fallback_failsafe = FallbackFailsafe(["fallback option 1", "fallback option 2"])
        result = loop.run_until_complete(
            fallback_failsafe.run(call)
        )

        assert result == "return value"

    def test_fallback_is_called_when_exception_is_raised(self):
        async def call(option):
            if option == "fallback option 1":
                raise Exception()
            elif option == "fallback option 2":
                return "return value"

        fallback_failsafe = FallbackFailsafe(["fallback option 1", "fallback option 2"])
        result = loop.run_until_complete(
            fallback_failsafe.run(call)
        )

        assert result == "return value"

    def test_exception_is_raised_when_no_fallback_succeeds(self):
        async def call(_):
            raise Exception()

        fallback_failsafe = FallbackFailsafe(["fallback option 1", "fallback option 2"])

        with pytest.raises(FallbacksExhausted):
            loop.run_until_complete(
                fallback_failsafe.run(call)
            )

    def test_args_are_passed_to_function(self):
        async def call(fallback_option, positional_argument, *args, **kwargs):
            assert fallback_option == "fallback option"
            assert positional_argument == "positional argument"
            assert args == ("arg1", "arg2")
            assert kwargs == {"key1": "value1", "key2": "value2"}

            return "return value"

        fallback_failsafe = FallbackFailsafe(["fallback option"])
        result = loop.run_until_complete(
            fallback_failsafe.run(call, "positional argument", "arg1", "arg2", key1="value1", key2="value2")
        )

        assert result == "return value"

    def test_original_exception_is_raised_and_fallback_is_not_executed_on_abortion(self):
        async def call(fallback_option):
            assert fallback_option == "fallback option1"
            raise ValueError()

        policy = RetryPolicy(abortable_exceptions=[ValueError])
        fallback_failsafe = FallbackFailsafe(["fallback option1", "fallback option2"],
                                             retry_policy_factory=lambda _: policy)
        with pytest.raises(ValueError):
            loop.run_until_complete(
                fallback_failsafe.run(call))
