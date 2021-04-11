import contextlib
import logging
import subprocess
import os
import tempfile

from .url import YTUrl


class YTVideo:
    def __init__(self, url: YTUrl):
        self._url = url

    @contextlib.contextmanager
    def make_clip_temp(self, duration: int, start=None):
        with mkstemp(".mp4") as video_file:
            self._make_clip(duration, video_file, start)
            yield video_file

    def _make_clip(self, duration: int, out_file: str, start=None):
        start = start if start is not None else self._url.timecode()
        # comes from https://old.reddit.com/r/youtubedl/comments/b67xh5/downloading_part_of_a_youtube_video/ejv5ye7/
        cmd = f"ffmpeg -ss {start} -i $(youtube-dl -f 22 -g {self._url.value()}) -acodec copy -vcodec copy -t {duration} {out_file} -y"  # noqa
        logging.info(cmd)
        p = subprocess.Popen(cmd, shell=True)
        p.wait()


@contextlib.contextmanager
def mkstemp(suffix=""):
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    yield path
    os.remove(path)
