# NFT Ownership
A service that allows to track NFT ownership changes by listening on-chain data. It stores NFT owners in Redis in form 
`{'<nft_contract>_<nft_token_id>': '<nft_owner_address>'}`

## CLI
### Stream
```shell
python main.py stream <NODE_URL>
```
Creates a filter for NFT `Transfer` events and poll it with a given `--sleep-interval`. If there are a new `Transfer` event, it updates NFT owner in Redis
### Get owner
```shell
python main.py get-owner <SOURCE> <NFT_CONTRACT> <TOKEN_ID>
```
Extracts owner of a given NFT whether from Redis of from blockchain. Pass `on_chain` as `<SOURCE>` to get owner directly 
from blockchain or `redis` to get it from DB


## Python API
### get_owner_redis
Params:
* `connector`: a `RedisConnector` object ([Example](https://github.com/ninjascant/nft-ownership/blob/main/nft_ownership/redis_utils.py#L4-L6))
* `user_metadata`: a dictionary with following fields:
    * `nft_contract` *(str)*: NFT contract address
    * `token_id` *(int)*: NFT token id