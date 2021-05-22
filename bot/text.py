from munch import munchify

text = munchify(
    {
        "url": {
            "question": "Please send video url",
        },
        "cancelled": "Cancelled.",
        "start": {
            "question": "Please select time the clip should start at",
            "choice": {
                "provide_timecode": "you chose to provide timecode",
                "url_timecode": "you chose to use timecode embedded in url",
                "from_start": "you chose to clip from start",
            },
            "timecode": {
                "question": "Please provide timecode in seconds",
                "invalid": "Timecode should have valid format\nPlease provide timecode (e.g. 5m20s)",
            },
        },
        "duration": {
            "question": "How long the clip should be in seconds?",
            "invalid": "Duration should be a number.\nHow long the clip should be in seconds? (digits only)",
        },
        # fmt: off
        "confirm": "URL: {url}\n"
                   "Duration: {duration} seconds\n"
                   "Start: {start}\n"
                   "Create clip?",
        # fmt: on
        "clip": {"creating": "Creating clip"},
    }
)
