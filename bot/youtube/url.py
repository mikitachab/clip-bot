import functools
import re
from urllib.parse import urlparse, parse_qs


class YTUrl:
    YT_URL_RE = r"^(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?(?:[^&]+)"

    def __init__(self, url):
        self._url = url

    @property
    def value(self):
        return self._url

    @functools.cached_property
    def timecode(self) -> int:
        return parse_qs(urlparse(self._url).query).get("t", [None])[0]

    @functools.cached_property
    def valid(self):
        return bool(re.match(self.YT_URL_RE, self._url))
