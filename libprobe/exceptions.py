from .severity import Severity
from typing import Optional


class IgnoreResultException(Exception):
    """IgnoreResultException must be raised by a check if the result needs
    to be ignored.

    - Nothing for this check will be returned to the AgentCore.
    - The check remains scheduled so there will be a next attempt.
    """
    pass


class IgnoreCheckException(Exception):
    """IgnoreResultException must be raised by a check if the result needs
    to be ignored and we no longer want this check to run.

    - Nothing for this check will be returned to the AgentCore.
    - The check will no longer be scheduled, unless new check configuration is
      received.
    """
    pass


class CheckException(Exception):
    """CheckException is the basic check exception."""
    def __init__(self, msg: str, severity: Severity = Severity.MEDIUM):
        assert msg, 'CheckException message must not be empty'
        self.severity = severity
        super().__init__(msg)

    def to_dict(self):
        return {
            "error": self.__str__(),
            "severity": self.severity.value
        }


class IncompleteResultException(CheckException):
    """IncompleteResultException must be raised when you want to return data
    together with a CheckError; With an empty result (empty dict), this
    exception will thus clear the previous check data.
    """
    def __init__(
            self,
            msg: str,
            result: dict,
            severity: Severity = Severity.MEDIUM):
        assert isinstance(result, dict)
        super().__init__(msg, severity=severity)
        self.result = result


class NoCountException(CheckException):
    """NoCountException must be raised when you do not want InfraSonar to
    count this check result. When a check result is not count, it will not seen
    by the last seen service. Conditions and time series data will be processed
    as usual.
    """
    def __init__(
            self,
            msg: str,
            result: dict,
            severity: Optional[Severity] = None):
        assert isinstance(result, dict)
        super().__init__(msg, severity=severity)
        self.result = result
