import redis


class RedisConnector:
    def __init__(self):
        self.conn = redis.Redis()


def get_last_block(connector, w3):
    last_block = connector.conn.get('last_block')
    if last_block is None:
        last_block = w3.eth.getBlock('latest')['number']
    else:
        last_block = int(last_block)
    return last_block


def set_last_block(logs, connector):
    last_block = max([log['block_number'] for log in logs])
    connector.conn.mset({'last_block': last_block})
    return last_block


def get_owner_redis(connector, user_metadata):
    nft_key = user_metadata['nft_address'] + '_' + int(user_metadata['token_id'])
    stored_owner = connector.conn.get(nft_key)

    return stored_owner
