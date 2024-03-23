import json

of_most_from_Eth_abi = json.load(open('./abis/bridge.json'))

sync_swap_router_abi = json.load(open('./abis/syncswap.json'))
stable_abi = json.load(open('./abis/erc20.json'))

ECHODEX_ROUTER_ABI = json.load(open('./abis/echodex.json'))
ECHODEX_CONTRACTS = "0xc66149996d0263C0B42D3bC05e50Db88658106cE"

DMAIL_ABI = json.load(open('./abis/dmail_abi.json'))
DMAIL_CONTRACT = "0xD1A3abf42f9E66BE86cfDEa8c5C2c74f041c5e14"

linea_swap_abi = json.load(open('./abis/lineaswap.json'))
linea_swap_contract = '0x3228d205a96409a07a44d39916b6ea7b765d61f4'

horizondex_router_abi = json.load(open('./abis/horizondex.json'))
horizondex_contract = '0x272E156Df8DA513C69cB41cC7A99185D53F926Bb'

layerbank_contract = '0x009a0b7c38b542208936f1179151cd08e2943833'
layerbank_abi = json.load(open('./abis/layerbank.json'))

layerbank_price_contract = '0x4F5F443fEC450fD64Dce57CCacE8f5ad10b4028f'
layerbank_price_abi = json.load(open('./abis/layerbank_price.json'))
