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

import logging

from failsafe import Failsafe, FailsafeError, CircuitBreaker, RetryPolicy

logger = logging.getLogger(__name__)


class FallbacksExhausted(FailsafeError):
    pass


class FallbackFailsafe:
    """
    This class provides a way of executing Failsafe calls in order to provide fallback functionality.
    """

    def __init__(self, fallback_data_list, retry_policy_factory=None, circuit_breaker_factory=None):
        """
        :param fallback_data_list: a list of objects which will differentiate between different fallback calls. An item
            from this list will be passed as the first parameter to the function provided to the run method.
        :param retry_policy_factory: factory function taking an item from fallback_data
            and returning a retry policy
        :param circuit_breaker_factory: factory function taking an item from fallback_data
            and returning a circuit breaker
        """

        retry_policy_factory = retry_policy_factory or (lambda _: RetryPolicy())
        circuit_breaker_factory = circuit_breaker_factory or (lambda _: CircuitBreaker())

        def _create_failsafe(data):
            return Failsafe(retry_policy=retry_policy_factory(data), circuit_breaker=circuit_breaker_factory(data))

        self.failsafe_list = [(data, _create_failsafe(data))
                              for data in fallback_data_list]

    async def run(self, callable, *args, **kwargs):
        for (fallback_data, failsafe) in self.failsafe_list:
            try:
                return await failsafe.run(lambda: callable(fallback_data, *args, **kwargs))
            except FailsafeError:
                logger.debug("Executing fallback callable")

        logger.debug("No more fallbacks")
        raise FallbacksExhausted("No more fallbacks")
