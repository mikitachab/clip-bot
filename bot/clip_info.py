from dataclasses import dataclass

import youtube as yt
import timecode as tc
from start_option import StartOption


@dataclass
class ClipInfo:
    url: yt.YTUrl
    duration: int
    start: int

    @staticmethod
    def from_data(data: dict):
        yt_url = yt.YTUrl(data["url"])
        if data["start"] == StartOption.from_start():
            start = 0
        else:
            start = tc.make_timecode(yt_url.timecode).seconds
        return ClipInfo(url=yt_url, duration=data["duration"], start=start)
