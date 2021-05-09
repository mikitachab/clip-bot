from munch import Munch

text = Munch(
    {
        "url": Munch(
            {
                "question": "Please send video url",
            }
        ),
        "cancelled": "Cancelled.",
        "duration": Munch(
            {
                "question": "How long clip should be?",
                "invalid": "Duration gotta be a number.\nHow long clip should be in seconds? (digits only)",
            }
        ),
        "start": Munch(
            {
                "question": "Start question?",  # FIXME pylint: disable=fixme
                "choice": Munch(
                    {
                        "provide_timecode": "you choosed to provide timecode",
                        "url_timecode": "you choosed use timecode",
                        "from_start": "you choosed from start",
                    }
                ),
                "timecode": Munch(
                    {
                        "question": "Please provide timecode in seconds",
                        "invalid": "Timecode should has valid format\nPlease provide timecode",
                    }
                ),
            }
        ),
        # fmt: off
        "confirm": "URL: {url}\n"
                   "Duration: {duration} seconds\n"
                   "Start: {start}\n"
                   "Create clip?",
        # fmt: on
    }
)
