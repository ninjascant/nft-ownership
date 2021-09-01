import json

with open('data/nft_abi.json') as json_file:
    nft_abi = json.load(json_file)


def get_contract_instance(w3, address, abi):
    address = w3.toChecksumAddress(address)
    return w3.eth.contract(address=address, abi=abi)


def topic_to_address(w3, topic):
    return '0x' + w3.toHex(topic)[-40:].lower()


def get_owner_on_chain(w3, user_metadata):
    nft_contract = get_contract_instance(w3, user_metadata['nft_contract'], nft_abi)
    owner = nft_contract.functions.ownerOf(user_metadata['token_id'].call())
    return owner
