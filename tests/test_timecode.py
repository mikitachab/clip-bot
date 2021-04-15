import pytest

from timecode import make_timecode, SecondsTimecode, FormattedTimecode, InvalidTimecodeError, is_valid_timecode


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
def test_make_timecode_raise_on_invalid_timecode(user_input):
    with pytest.raises(InvalidTimecodeError):
        make_timecode(user_input)


@pytest.mark.parametrize(
    "timecode, is_valid",
    [
        ("123", True),
        ("234s", True),
        ("30m", True),
        ("30m20s", True),
        ("some text", False),
        ("3s5h", False),
        ("234s234", False),
        (None, False),
    ],
)
def test_is_valid_timecode(timecode, is_valid):
    assert is_valid_timecode(timecode) == is_valid
