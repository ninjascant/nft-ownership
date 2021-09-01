import click

from .stream import stream_updates
from .get_nft_owner import get_owner


@click.group()
def run():
    pass


run.add_command(stream_updates, 'stream')
run.add_command(get_owner, 'get-owner')
