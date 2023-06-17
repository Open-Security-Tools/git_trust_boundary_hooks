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
    from .ops import Operations
    Operations().pre_commit_hook()


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
    from .ops import Operations

    with open(commit_message_file, "r") as f:
        message = f.read()

    Operations().commit_message_hook(message=message)


@click.command()
@click.option(
    "--verbose",
    is_flag=True,
    callback=_setup_logging,
    expose_value=False,
    is_eager=True,
    help="Enable DEBUG logging level")
@click.argument("name")
@click.argument("location")
def tbh_hook_pre_push(name, location):
    """ Git hook run before push """
    from .ops import Operations

    Operations().pre_push_hook()


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


@tbh_utils.command("refresh")
def update_bad_symbols():
    """ Refresh the bad symbol list from Minio object store
    """
    from .template import Template
    Template().update_bad_symbols()


@tbh_utils.command("scan")
def scan():
    """ Scan git history and untracked files
    """
    from .ops import Operations
    operations = Operations()
    operations.scan_git_history()
    operations.scan_untracked_files()
    operations.scan_cached_files()
    operations.assert_no_errors()


@tbh_utils.command("bad-symbols")
def print_bad_symbols():
    """ Display the contents of the bad symbols file
    """
    from .template import Template
    bad_symbols_path = Template().bad_symbols_path
    with open(bad_symbols_path, "r") as f:
        print(f.read())


@tbh_utils.command("paths")
def scan():
    """ Display the locations of utilities and templates
    """
    from .template import Template
    t = Template()
    print(f"Bad symbols file: '{t.bad_symbols_path}'")
    print(f"Global template directory: '{t.global_template_path}'")
    print(f"Minio Configuration file: '{t.minio_configuration_path}'")
