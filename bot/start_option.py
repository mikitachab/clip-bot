class StartOption:
    def __init__(self, option):
        self._option = option

    def text(self) -> str:
        if self._option == StartOption.from_start():
            return "from video start"
        return self._option.split(";")[1]

    @staticmethod
    def from_start() -> str:
        return "from_start;"

    @staticmethod
    def timecode(timecode_str) -> str:
        return f"timecode;{timecode_str}"
