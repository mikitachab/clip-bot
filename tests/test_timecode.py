import pytest

from bot.timecode import make_timecode, SecondsTimecode, FormattedTimecode, InvalidTimecodeError


@pytest.mark.parametrize(
    "user_input, timecode_cls, expected_seconds",
    [
        ("123", SecondsTimecode, 123),
        ("234s", FormattedTimecode, 234),
        ("30m", FormattedTimecode, 1800),
        ("30m20s", FormattedTimecode, 1820),
    ],
)
def test_make_timecode(user_input, timecode_cls, expected_seconds):
    t = make_timecode(user_input)
    assert isinstance(t, timecode_cls)
    assert t.seconds == expected_seconds


@pytest.mark.parametrize(
    "user_input",
    [
        "some text",
        "3s5h",
    ],
)
def test_raise_on_invalid_timecode(user_input):
    with pytest.raises(InvalidTimecodeError):
        make_timecode(user_input)
