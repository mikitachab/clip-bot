import dataclasses
import subprocess
import re
from typing import Optional

class YouTubeVideo:
    
    def __init__(self, url: str):
        self.url = url
    
    @property
    def timecode(self) -> int:
        match = re.search(r".+\?t=(\d+)", self.url)
        if match and hasattr(match, "groups"):
            return match.groups()[0]
        return 0


    def make_clip(self, duration: int, out_file: str):
        # comes from https://old.reddit.com/r/youtubedl/comments/b67xh5/downloading_part_of_a_youtube_video/ejv5ye7/     
        cmd = f"ffmpeg -ss {self.timecode} -i $(youtube-dl -f 22 -g {self.url}) -acodec copy -vcodec copy -t {duration} {out_file} -y"
        print(cmd)
        p = subprocess.Popen(cmd, shell=True)
        p.wait()
