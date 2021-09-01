import json
import redis
import json
from urllib.parse import urlparse


class StorageClient:
    def __init__(self, url=False):
        self.url = url
        self.storage = {}
        print(self.url)
        if self.url != 'localhost':
            print("Production Redis connecting..")
            url = urlparse(url)
            self.r = redis.Redis(host=url.hostname, port=url.port, username=url.username, password=url.password, ssl=True, ssl_cert_reqs=None)
        else:
            print("Dev Redis connecting...")
            self.r = redis.Redis("localhost")

    def read(self, id):
        try:
            return json.loads(self.r.get(id))
        except Exception as e:
            return {}

    def write(self, id, data):
        data = json.dumps(data)
        self.r.set(id, data)


def get_last_block(connector, w3):
    last_block = connector.read('last_block')
    print(last_block)
    if not last_block:
        last_block = w3.eth.getBlock('latest')['number']
    else:
        last_block = int(last_block)
    return last_block


def set_last_block(logs, connector):
    last_block = max([log['block_number'] for log in logs])
    connector.write('last_block', last_block)
    return last_block


def get_owner_redis(connector, user_metadata):
    nft_key = user_metadata['nft_contract'] + '_' + str(user_metadata['token_id'])
    stored_owner = connector.read(nft_key)

    return stored_owner
