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


class RetryPolicy:
    """
    Model to store the number of allowed retries, the allowed retriable exceptions
    and the exceptions that should abort the failsafe run.
    """

    def __init__(self, allowed_retries=3, retriable_exceptions=None, abortable_exceptions=None):
        """
        Constructs RetryPolicy.

        :param allowed_retries: number indicating how many retries can be performed. 0 means no retries.
        :param retriable_exceptions: list of exception types indicating which exceptions can cause a retry. If None
            every exception is considered retriable
        :param abortable_exceptions: list of exception types indicating which exceptions should abort failsafe run
            immediately and be propagated out of failsafe. If None, no exception is considered abortable.
        """
        self.allowed_retries = allowed_retries
        self.retriable_exceptions = retriable_exceptions
        self.abortable_exceptions = abortable_exceptions

    def should_retry(self, context, exception):
        """
        Returns a boolean indicating if a retry should be performed taking into
        account the number of attempts already performed and the retriable_exceptions.

        :param context: :class:`failsafe.failsafe.Context`.
        :param exception: Exception which caused failure to be considered
            retriable or not raised during the execution.
        """
        return context.attempts <= self.allowed_retries and self._is_retriable_exception(exception)

    def should_abort(self, exception):
        """
        Returns a boolean indicating whether failsafe run should be aborted and exception propagated
        outside the failsafe.

        :param exception: Exception which caused failure to be considered
            abortable or not during the execution.
        """
        if self.abortable_exceptions is None:
            return False

        return any(isinstance(exception, e) for e in self.abortable_exceptions)

    def _is_retriable_exception(self, exception):
        if self.retriable_exceptions is None:
            return True

        return any(isinstance(exception, e) for e in self.retriable_exceptions)
