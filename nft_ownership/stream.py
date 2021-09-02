import time
import click
import json
import itertools
from web3 import Web3, HTTPProvider
from discord_webhook import DiscordWebhook

from .redis_utils import StorageClient, get_last_block, set_last_block
from .web3_utils import topic_to_address, get_contract_instance

with open('data/nft_abi.json') as json_file:
    nft_abi = json.load(json_file)

with open('config.json') as json_file:
    config = json.load(json_file)

NFT_TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
WEBHOOK_URL = config['discord_webhook_url']


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
    }
    return parsed_event


def filter_nft_transfers(logs):
    return [log for log in logs if len(log['topics']) > 2]


def get_balance(contract, address):
    return int(contract.functions.balanceOf(address).call())


def send_message(message_text, webhook):
    webhook = DiscordWebhook(url=webhook, content=message_text)
    response = webhook.execute()
    return response


def check_balances(w3, connector, transfers):
    transfers = sorted(transfers, key=lambda x: x['contract_address'])
    senders = {log['from_address'] for log in transfers}
    transfers_by_token = itertools.groupby(transfers, key=lambda x: x['contract_address'])

    discord_data = connector.read('discord')

    for token, transfers in transfers_by_token:
        token_contract = get_contract_instance(w3, token, nft_abi)
        token_channel = discord_data.get(token)
        if not token_channel:
            continue
        token_users = token_channel['users'].values()

        kicked_users = []

        for user in token_users:
            if user['address'] in senders:
                user['owns'] = get_balance(token_contract, w3.toChecksumAddress(user['address']))

                should_kick = user['owns'] < token_channel['minBalance']

                if should_kick:
                    print(f'User {user["address"]} should be kicked')
                    user['isQualified'] = False
                    kicked_users.append(user['address'])

        connector.write('discord', discord_data)

        send_message(
            f".allow_user_from_record {token} {kicked_users[0]} ",
            WEBHOOK_URL
        )


def parse_and_update(new_logs, connector, w3):
    filtered_logs = filter_nft_transfers(new_logs)
    parsed_logs = [parse_nft_transfer(w3, log) for log in filtered_logs]

    if len(parsed_logs) != 0:
        check_balances(w3, connector, parsed_logs)
        last_block = set_last_block(parsed_logs, connector)
        print(f'Found {len(parsed_logs)} transfers. Last synced block: {last_block}')


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
