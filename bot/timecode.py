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
        self._extracted: bool = False

    def _extract_timecode(self):
        if self._extracted:
            return
        hours, minutes, seconds = re.match(self.PATTERN, self._text).groups()
        if hours:
            self._houres = int(hours)
        if minutes:
            self._minutes = int(minutes)
        if seconds:
            self._seconds = int(seconds)
        self._extracted = True

    @property
    def seconds(self) -> int:
        self._extract_timecode()
        return self._seconds + self._minutes * 60 + self._houres * 3600

    def __str__(self) -> str:
        return self._text


def make_timecode(text: str):
    if re.match(SecondsTimecode.PATTERN, text):
        return SecondsTimecode(text)
    if re.match(FormattedTimecode.PATTERN, text):
        return FormattedTimecode(text)
    raise InvalidTimecodeError


def is_valid_timecode(timecode):
    return timecode is not None and any(
        re.match(timecode_cls.PATTERN, timecode) for timecode_cls in [SecondsTimecode, FormattedTimecode]
    )
