import abc
import re


class InvalidTimecodeError(Exception):
    pass


class TimecodeInterface(abc.ABC):
    @property
    @abc.abstractmethod
    def seconds(self) -> int:
        raise NotImplementedError


class SecondsTimecode(TimecodeInterface):
    PATTERN = r"^\d+$"

    def __init__(self, text: str):
        self._seconds = int(text)

    @property
    def seconds(self) -> int:
        return self._seconds


class FormattedTimecode(TimecodeInterface):

    PATTERN = r"^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$"

    def __init__(self, text: str):
        self._text = text
        self._seconds: int = 0
        self._minutes: int = 0
        self._houres: int = 0
        self._extract_timecode()

    def _extract_timecode(self):
        h, m, s = re.match(self.PATTERN, self._text).groups()
        if h:
            self._houres = int(h)
        if m:
            self._minutes = int(m)
        if s:
            self._seconds = int(s)

    @property
    def seconds(self) -> int:
        return self._seconds + self._minutes * 60 + self._houres * 3600


def make_timecode(text: str):
    if re.match(SecondsTimecode.PATTERN, text):
        return SecondsTimecode(text)
    if re.match(FormattedTimecode.PATTERN, text):
        return FormattedTimecode(text)
    raise InvalidTimecodeError
