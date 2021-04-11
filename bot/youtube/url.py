import re
import functools


class YTUrl:
    def __init__(self, url):
        self._url = url

    def value(self):
        return self._url

    @functools.cached_property
    def timecode(self) -> int:
        match = re.search(r".+\?t=(\d+)", self._url)
        if match and hasattr(match, "groups"):
            return match.groups()[0]
        return 0
