import time
import click
from web3 import Web3, HTTPProvider

from .redis_utils import StorageClient, get_last_block, set_last_block
from .web3_utils import topic_to_address

NFT_TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'


def construct_nft_id(log):
    return log['contract_address'].lower() + '_' + str(log['token_id'])


def update_ownership(logs, connector):
    for log in logs:
        log_nft_id = construct_nft_id(log)
        log_owner = log['to_address'].lower()
        connector.write(log_nft_id, log_owner)


def parse_nft_transfer(w3, transfer):
    parsed_event = {
        'contract_address': transfer['address'].lower(),
        'block_number': transfer['blockNumber'],
        'transaction_hash': w3.toHex(transfer['transactionHash']),
        'log_index': transfer['logIndex'],
        'from_address': topic_to_address(w3, transfer['topics'][1]),
        'to_address': topic_to_address(w3, transfer['topics'][2]),
        'token_id': w3.toInt(transfer['topics'][3])
    }
    return parsed_event


def filter_nft_transfers(logs):
    return [log for log in logs if len(log['topics']) == 4]


def parse_and_update(new_logs, connector, w3):
    filtered_logs = filter_nft_transfers(new_logs)
    parsed_logs = [parse_nft_transfer(w3, log) for log in filtered_logs]

    if len(parsed_logs) != 0:
        update_ownership(parsed_logs, connector)
        last_block = set_last_block(parsed_logs, connector)
        print(f'Found {len(parsed_logs)} NFT transfers. Last synced block: {last_block}')


@click.command()
@click.argument('node_url', type=str)
@click.option('-r', '--redis-url', type=str, default='localhost')
@click.option('-l', '--last-block', type=int, default=None)
@click.option('-s', '--sleep-interval', type=float, default=1.5)
def stream_updates(node_url, redis_url, last_block, sleep_interval):
    connector = StorageClient(redis_url)

    w3 = Web3(HTTPProvider(node_url))

    if last_block is None:
        last_block = get_last_block(connector, w3)
    print(f'Start syncing from block {last_block}')

    log_filter = w3.eth.filter({'topics': [NFT_TRANSFER_TOPIC], 'fromBlock': last_block})

    new_logs = log_filter.get_all_entries()
    parse_and_update(new_logs, connector, w3)

    while True:
        new_logs = log_filter.get_new_entries()
        parse_and_update(new_logs, connector, w3)

        time.sleep(sleep_interval)
