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


class ExceptionHandlingPolicy:
    """
    Model to store the number of allowed retries, the allowed retriable exceptions
    and the exceptions that should be re-raised
    """

    def __init__(self, allowed_retries=3, retriable_exceptions=None, raisable_exceptions=None):
        self.allowed_retries = allowed_retries
        if retriable_exceptions is None:
            retriable_exceptions = []
        self.retriable_exceptions = retriable_exceptions
        if raisable_exceptions is None:
            raisable_exceptions = []
        self.raisable_exceptions = raisable_exceptions

    def should_retry(self, context, exception=None):
        """
        Returns a boolean indicating if a retry should be performed taking into
        account the number of attempts already performed and the retriable_exceptions.

        :param context: :class:`failsafe.failsafe.Context`.
        :param exception: Exception which caused failure to be considered
            retriable or not raised during the execution.
        """
        return context.attempts <= self.allowed_retries and self._is_expected_exception(exception)

    def _is_expected_exception(self, exception):
        return any(isinstance(exception, e) for e in self.retriable_exceptions) if self.retriable_exceptions else True


    def should_raise(self, exception=None):
        """
        Returns a boolean indicating if we should raise and propagate the given exception
        outside the failsafe

        :param context: :class:`failsafe.failsafe.Context`.
        :param exception: Exception which caused failure to be considered
            raisable or not raised during the execution.
        """
        return any(isinstance(exception, e) for e in self.raisable_exceptions) if self.raisable_exceptions else False
