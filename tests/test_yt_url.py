import pytest

from youtube import YTUrl


@pytest.mark.parametrize(
    "url, timecode",
    [
        ("https://www.youtube.com/watch?v=id&t=100", "100"),
        ("https://www.youtube.com/watch?v=id&t=3m4s", "3m4s"),
        ("https://www.youtube.com/watch?v=id&t=5h3m4s&other=value", "5h3m4s"),
        ("https://www.youtube.com/watch?v=id", None),
    ],
)
def test_url_timecode(url, timecode):
    assert YTUrl(url).timecode == timecode


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=id&t=100",
        "https://www.youtube.com/watch?v=id&t=3m4s",
        "https://www.youtube.com/watch?v=id&t=5h3m4s&other=value",
    ],
)
def test_url_value(url):
    assert YTUrl(url).value == url


@pytest.mark.parametrize(
    "url, valid",
    [
        ("https://www.youtube.com/watch?v=id&t=100", True),
        ("https://www.youtube.com/watch?v=id&t=3m4s", True),
        ("https://www.youtube.com/watch?v=id&t=5h3m4s&other=value", True),
        ("https://youtu.be/FdeioVndUhs", True),
        ("https://www.youtu.be/FdeioVndUhs", True),
        ("https://www.you.tube/watch?v=FdeioVndUhs", False),
        ("https://you.tube/watch?v=FdeioVndUhs", False),
        ("https://www.yout.ube/watch?v=FdeioVndUhs", False),
    ],
)
def test_url_valid(url, valid):
    assert YTUrl(url).valid is valid
