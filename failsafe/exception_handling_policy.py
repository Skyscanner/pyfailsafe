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
    and the exceptions that should abort the failsafe run
    """

    def __init__(self, allowed_retries=3, retriable_exceptions=None, abortable_exceptions=None):
        self.allowed_retries = allowed_retries
        if retriable_exceptions is None:
            retriable_exceptions = []
        self.retriable_exceptions = retriable_exceptions
        if abortable_exceptions is None:
            abortable_exceptions = []
        self.abortable_exceptions = abortable_exceptions

    def should_retry(self, context, exception=None):
        """
        Returns a boolean indicating if a retry should be performed taking into
        account the number of attempts already performed and the retriable_exceptions.

        :param context: :class:`failsafe.failsafe.Context`.
        :param exception: Exception which caused failure to be considered
            retriable or not raised during the execution.
        """
        return context.attempts <= self.allowed_retries and self._is_retriable_exception(exception)

    def _is_retriable_exception(self, exception):
        return any(isinstance(exception, e) for e in self.retriable_exceptions) if self.retriable_exceptions else True

    def should_abort(self, exception=None):
        """
        Returns a boolean indicating if we should abort the run and propagate the given exception
        outside the failsafe

        :param exception: Exception which caused failure to be considered
            abortable or not during the execution.
        """
        return any(isinstance(exception, e) for e in self.abortable_exceptions) if self.abortable_exceptions else False
