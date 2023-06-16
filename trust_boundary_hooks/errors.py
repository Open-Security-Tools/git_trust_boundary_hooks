import click

FAIL_COLOUR_CODE = '\033[91m'


class TBHBaseError(click.ClickException):

    def show(self, file=None) -> None:
        click.secho(f"Esdfrror: {self.format_message()}", file=file, fg="red")


class CannotOverwriteTemplateDirectoryError(TBHBaseError):
    pass


class MinioConfigError(TBHBaseError):
    pass


class MinioObjectMissingError(TBHBaseError):
    pass


class BadSymbolsDetectedError(TBHBaseError):
    pass
