import logging
import os
import os.path
import shutil
from pathlib import Path

import click
from click_plugins import with_plugins

from . import __version__
from .backends import guess_backend, list_backends
from .conf import FileConfig
from .core import Context
from .utils import ColorFormatter, entry_points, find_workflow

logger = logging.getLogger(__name__)


BASIC_FORMAT = "%(message)s"

ADVANCED_FORMAT = "%(levelname)s%(message)s"

LOGGING_FORMATS = {
    "warning": BASIC_FORMAT,
    "info": BASIC_FORMAT,
    "debug": ADVANCED_FORMAT,
    "error": BASIC_FORMAT,
}

def get_level(level):
    return getattr(logging, level.upper())


def configure_logging(level_name):
    fmt = LOGGING_FORMATS[level_name]

    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter(fmt=fmt))

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(get_level(level_name))
    return root


@with_plugins(entry_points(group="gwf.plugins"))
@click.group(context_settings={"obj": {}})
@click.version_option(version=__version__)
@click.option("-e", "--environment", default="sjup", help="Conda environment to activate on the cluster.")
@click.option(
    "-b",
    "--backend",
    type=click.Choice(list_backends()),
    help="Backend used to run workflow.",
)
@click.option(
    "-v",
    "--verbose",
    type=click.Choice(["warning", "debug", "info", "error"]),
    default="info",
    help="Verbosity level.",
)
@click.pass_context
def main(ctx, address, backend, verbose):
    """A flexible, pragmatic workflow tool.

    See help for each command using the `--help` flag for that command:

        sjup serve --help

    Shows help for the serve command.
    """
    configure_logging(level_name=verbose)

    try:
        pass
    except FileNotFoundError:
        click.confirm(
            "Could not find a workflow file! Do you want to create one in this directory?",
            abort=True,
        )
    working_dir = Path.cwd()

    # Instantiate workflow config directory.
    working_dir.joinpath(".sjup").mkdir(exist_ok=True)
    working_dir.joinpath(".sjup", "logs").mkdir(exist_ok=True)

    config = FileConfig.load(working_dir.joinpath(".sjupconf.json"))

    # # If the --use-color/--no-color argument is not set, get a value from the
    # # configuration file. If nothing has been configured, check if the NO_COLOR
    # # environment variable has been set.
    # if no_color is None:
    #     if config.get("no_color") is None:
    #         no_color = bool(os.getenv("NO_COLOR", False))
    #     else:
    #         no_color = config["no_color"]

    # if no_color:
    #     # Hack for disabling all click colors. We basically lie to
    #     # click and pretend that the shell is never a TTY.
    #     click._compat.isatty = lambda s: False

    backend = backend or config.get("backend")
    if backend is None:
        logger.debug("No backend was configured, guessing a backend instead")
        score, backend = guess_backend()
        logger.debug("Found backend '%s' with priority %s", backend, score)
    logger.debug("Using '%s' backend", backend)

    ctx.obj = Context(
        working_dir=str(working_dir),
        config=config,
        backend=backend,
        address=address,
    )