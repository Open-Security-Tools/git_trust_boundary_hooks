FAIL_COLOUR_CODE = '\033[91m'


class ExitWithMessageError(Exception):

    def display(self) -> None:
        print(f"{FAIL_COLOUR_CODE}Error: {self.message}")

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
