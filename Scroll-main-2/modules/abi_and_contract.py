import json

bridge_deposit_abi = json.load(open('./abis/deposit.json'))

bridge_oracle_abi = json.load(open('./abis/oracle.json'))

WETH_ABI = json.load(open('./abis/weth.json'))

DMAIL_ABI = json.load(open('./abis/dmail.json'))

stable_abi = json.load(open('./abis/erc20.json'))

layerbank_abi = json.load(open('./abis/layerbank.json'))

SYNCSWAP_ROUTER_ABI = json.load(open('./abis/router.json'))

SYNCSWAP_CLASSIC_POOL_ABI = json.load(open('./abis/classic_pool.json'))

SYNCSWAP_CLASSIC_POOL_DATA_ABI = json.load(open('./abis/classic_pool_data.json'))

SKYDROME_ROUTER_ABI = json.load(open('./abis/skydrome.json'))

DEPLOYER_ABI = json.load(open("./abis/abi.json"))

NFT_ORIGINS_ABI = json.load(open("./abis/nft_mint.json"))

AMBIENT_SWAP_ABI = json.load(open("./abis/ambient_swap.json"))

IZUMI_QUOTER_ABI = json.load(open("./abis/izumi_quoter.json"))
IZUMI_ROUTER_ABI = json.load(open("./abis/izumi_router.json"))



with open("./abis/bytecode.txt", "r") as file:
    DEPLOYER_BYTECODE = file.read()

BRIDGE_CONTRACTS = {
    "deposit": "0xf8b1378579659d8f7ee5f3c929c2f3e332e41fd6",
    "withdraw": "0x4C0926FF5252A435FD19e10ED15e5a249Ba19d79",
    "oracle": "0x987e300fDfb06093859358522a79098848C33852",
}

SCROLL_TOKENS = {
    "ETH": "0x5300000000000000000000000000000000000004",
    "WETH": "0x5300000000000000000000000000000000000004",
    "USDC": "0x06eFdBFf2a14a7c8E15944D1F4A48F9F95F663A4",
}

SYNCSWAP_CONTRACTS = {
    "router": "0x80e38291e06339d10aab483c65695d004dbd5c69",
    "classic_pool": "0x37BAc764494c8db4e54BDE72f6965beA9fa0AC2d",
}

SKYDROME_CONTRACTS = {
    "router": "0xAA111C62cDEEf205f70E6722D1E22274274ec12F",
}

DMAIL_CONTRACT = "0x47fbe95e981c0df9737b6971b451fb15fdc989d9"

LAYERBANK_CONTRACT = '0xec53c830f4444a8a56455c6836b5d2aa794289aa'

LAYERBANK_WETH_CONTRACT = '0x274C3795dadfEbf562932992bF241ae087e0a98C'

NFT_ORIGINS_CONTRACT = "0x74670A3998d9d6622E32D0847fF5977c37E0eC91"

AMBIENT_CONTRACT = "0xaaaaAAAACB71BF2C8CaE522EA5fa455571A74106"

IZUMI_QUOTER_CONTRACT = "0x3EF68D3f7664b2805D4E88381b64868a56f88bC4"
IZUMI_ROUTER_CONTRACT = "0x2db0AFD0045F3518c77eC6591a542e326Befd3D7"
