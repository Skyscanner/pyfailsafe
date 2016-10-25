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


class RaisePolicy:
    """
    Model to store the exceptions that can escape the failsafe
    """

    def __init__(self, raisable_exceptions=None):
        self.raisable_exceptions = raisable_exceptions

    def should_raise(self, exception=None):
        """
        Returns a boolean indicating if we should raise and propagate the given exception
        outside the failsafe

        :param context: :class:`failsafe.failsafe.Context`.
        :param exception: Exception which caused failure to be considered
            raisable or not raised during the execution.
        """
        return any(isinstance(exception, e) for e in self.raisable_exceptions) if self.raisable_exceptions else False
