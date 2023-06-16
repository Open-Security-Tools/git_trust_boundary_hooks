import click
import logging
from .aliased_group import AliasedGroup
from . import errors

log = logging.getLogger(__name__)


# noinspection PyUnusedLocal
def _setup_logging(ctx, obj, verbose):
    import click_log

    handler = click_log.ClickHandler()
    handler.formatter = click_log.ColorFormatter()
    handler.formatter.colors["info"] = dict(fg="magenta")

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        handlers=[handler, ],
    )

    if log.isEnabledFor(logging.DEBUG):
        log.debug("Verbose logging enabled")

    return verbose


@click.command()
@click.option(
    "--verbose",
    is_flag=True,
    callback=_setup_logging,
    expose_value=False,
    is_eager=True,
    help="Enable DEBUG logging level")
def tbh_setup():
    """
    Sets up git hooks in this environment:

    \b
    1. Creates the git template directory ~/.git-template
    2. Sets up a hooks subdirectory with symlinks
    3. Calls git set the global configuration for template hooks
    5. Prompts for credentials to access the Minio object store with bad symbols
    6. Stores the bad symbols in ~/.badsymbols

    Manages the following hooks:

    \b
    - commit-msg
    - pre-commit
    - pre-push

    """
    from .template import Template
    Template().setup()


@click.command()
@click.option(
    "--verbose",
    is_flag=True,
    callback=_setup_logging,
    expose_value=False,
    is_eager=True,
    help="Enable DEBUG logging level")
def tbh_hook_pre_commit():
    """ Git hook run before commit
    """
    from .scan import Scanner
    import subprocess
    import os
    from bs4 import UnicodeDammit

    scanner = Scanner()

    output = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM']).decode('utf-8')
    files = output.splitlines(keepends=False)

    log.info(f"Looking for bad symbols in files: {files}...")

    for fn in files:
        with open(fn, "rb") as f:
            # We use a utility to manage detection and decoding.
            dammit = UnicodeDammit(f.read())

        log.debug(f"Original Encoding of {fn} = {dammit.original_encoding}")

        scanner.scan_string(context=f"File({fn})", value=dammit.unicode_markup)
        
    log.info("Looking for bad symbols in git author metadata...")
    name = os.environ.get("GIT_AUTHOR_NAME")
    email = os.environ.get("GIT_AUTHOR_EMAIL")
    scanner.scan_string(context="GitAuthor", value=name)
    scanner.scan_string(context="GitEmail", value=email)

    if scanner.detections:
        log.error(f"Detection of {len(scanner.detections)} bad symbol(s)!")
        scanner.display_detections()
        raise errors.BadSymbolsDetectedError("Bad symbols detected in local changes!")


@click.command()
@click.option(
    "--verbose",
    is_flag=True,
    callback=_setup_logging,
    expose_value=False,
    is_eager=True,
    help="Enable DEBUG logging level")
@click.argument("commit_message_file")
def tbh_hook_commit_msg(commit_message_file):
    """ Git hook run on commit message """
    from .scan import Scanner
    log.info("Looking for bad symbols in the commit message...")

    with open(commit_message_file, "r") as f:
        message = f.read()

    scanner = Scanner()
    scanner.scan_string(context="CommitMessage", value=message)
    if scanner.detections:
        log.error(f"Detection of {len(scanner.detections)} bad symbol(s)!")
        scanner.display_detections()
        raise errors.BadSymbolsDetectedError("Bad symbols detected in commit message!")


@click.group(cls=AliasedGroup, invoke_without_command=True)
@click.option(
    "--verbose",
    is_flag=True,
    callback=_setup_logging,
    expose_value=False,
    is_eager=True,
    help="Enable DEBUG logging level")
@click.pass_context
def tbh_utils(ctx):
    """ tbh-utils

    Trust Boundary Hooks utility commands.    

    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help(), color=ctx.color)
        ctx.exit()


@tbh_utils.command("update-bad-symbols")
def update_bad_symbols():
    """ Refresh the bad symbol list from Minio object store
    """
    from .template import Template
    Template().update_bad_symbols()
