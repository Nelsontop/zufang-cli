from __future__ import annotations

import logging

import click

from . import __version__
from .commands.meta import cities, providers
from .commands.search import export, open_command, search, show


@click.group()
@click.version_option(version=__version__, prog_name="zufang")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose request logging.")
def cli(verbose: bool) -> None:
    if verbose:
        logging.basicConfig(level=logging.INFO, format="%(name)s %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)


cli.add_command(search)
cli.add_command(show)
cli.add_command(open_command)
cli.add_command(export)
cli.add_command(providers)
cli.add_command(cities)


if __name__ == "__main__":
    cli()
