import click
from web3 import Web3, HTTPProvider
from .web3_utils import get_owner_on_chain
from .redis_utils import get_owner_redis, StorageClient


@click.command()
@click.argument('source', type=str)
@click.argument('nft_contract', type=str)
@click.argument('token_id', type=int)
@click.option('-r', '--redis-url', type=str, default='localhost')
@click.option('-u', '--node-url', type=str)
def get_owner(source, nft_contract, token_id, redis_url, node_url):
    metadata = {
        'nft_contract': nft_contract,
        'token_id': token_id
    }
    if source == 'on_chain':
        w3 = Web3(HTTPProvider(node_url))
        owner = get_owner_on_chain(w3, metadata)
    else:
        connector = StorageClient(redis_url)
        owner = get_owner_redis(connector, metadata)

    print(f'Owner of NFT with contract address {nft_contract} and token id {token_id} is {owner}')