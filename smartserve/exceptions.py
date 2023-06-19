class NotEnoughTestDataError(StopIteration):
    """
        Not enough test data values were available, to generate a value for the
        given field from the test data JSON file.
    """

    DEFAULT_MESSAGE = "Not enough test data values were available, to generate one from the test data JSON file."

    def __init__(self, message: str | None = None, field_name: str | None = None) -> None:
        self.message: str = message or self.DEFAULT_MESSAGE
        self.field_name: str | None = field_name

        super().__init__(message or self.DEFAULT_MESSAGE)

    def __str__(self) -> str:
        """
            Returns formatted message & properties of the
            NotEnoughTestDataError.
        """

        return f"{self.message} (field_name={repr(self.field_name)})"
