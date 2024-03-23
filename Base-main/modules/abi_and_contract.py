import json

BASE_BRIDGE_ABI = json.load(open('./abis/bridge.json'))

WETH_ABI = json.load(open('./abis/weth.json'))

BASESWAP_ROUTER_ABI = json.load(open('./abis/baseswap.json'))

COLATERAL_AAVE_ABI = json.load(open('./abis/colateral_aave.json'))

AAVE_ABI = json.load(open('./abis/aave.json'))

ALIEN_ROUTER_ABI = json.load(open('./abis/alienswap.json'))

stable_abi = json.load(open('./abis/erc20.json'))

DMAIL_ABI = json.load(open('./abis/dmail.json'))

BASE_TOKENS = {
    "ETH": "0x4200000000000000000000000000000000000006",
    "WETH": "0x4200000000000000000000000000000000000006",
    "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
}

ODOS_CONTRACT = {
    "router": "0x19ceead7105607cd444f5ad10dd51356436095a1",
}

BASESWAP_CONTRACTS = {
    "router": "0x327Df1E6de05895d2ab08513aaDD9313Fe505d86"
}

ALIEN_CONTRACTS = {
    "router": "0x8c1a3cf8f83074169fe5d7ad50b978e1cd6b37c7"
}

BASE_BRIDGE_CONTRACT = "0x49048044D57e1C92A77f79988d21Fa8fAF74E97e"

AAVE_CONTRACT = "0x18cd499e3d7ed42feba981ac9236a278e4cdc2ee"

AAVE_WETH_CONTRACT = "0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7"

DMAIL_CONTRACT = "0x47fbe95e981C0Df9737B6971B451fB15fdC989d9"
