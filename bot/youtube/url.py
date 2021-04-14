import functools
from urllib.parse import urlparse, parse_qs


class YTUrl:
    def __init__(self, url):
        self._url = url

    @property
    def value(self):
        return self._url

    @functools.cached_property
    def timecode(self) -> int:
        return parse_qs(urlparse(self._url).query).get("t", [None])[0]
