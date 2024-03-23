# время между транзакциями/аккаунтами Bridge RhinoFi
PAUSA_MIN = 240
PAUSA_MAX = 360

# повтор транзакций после ошибки, больше 1 есть риск словить много подряд ошибок, одной обычно хватает
POVTOR_TX = 2

# для контроля GWEI, чтобы скрипт останавливался, если газ большой
GWEI_CONTROL = 40

# True или False, если стоит True будет для каждого аккаунта использовать прокси из файла (формат ip:port:log:pass)
USE_PROXY = False

# мешает кошельки
SHUFFLE_WALLET = True

RPC_SCROLL = 'https://rpc.ankr.com/scroll'

################## RHINOFI BRIDGE SETTINGS ###################
##############################################################
RETRY = 3 # кол-во попыток при ошибках / фейлах
GWEI_MULTIPLIER = 1.1
TIME_TO_WAIT = 5 # время ожидания баланса в Scroll после бриджа в минутах

PROXY = 'http://log:pass@ip:port' # чтобы не использовать прокси - оставьте как есть
CHANGE_IP_LINK = 'https://changeip.mobileproxy.space/?proxy_key=...&format=json' # чтобы не использовать ссылку для смены айпи - оставьте как есть

SCROLL_MIN_BALANCE = 0.02 # если баланс в Scroll будет больше указанного - бриджить в Scroll не будет
MAX_DIFFERENCE = 0.00060679 # максимальная разница в ETH между `сколько_отправить` - `сколько_получить`

RHINO_BRIDGE_VALUES = {
    # 'arbitrum': [0.001, 0.0012], # бриджить из Arbitrum в Scroll от 0.001 ETH до 0.0012 ETH
    # 'optimism': [0.001, 0.0012],
    # 'base':     [0.001, 0.0012],
    'zksync':   [0.018, 0.022],
}

RPCS = {
    'ethereum': 'https://rpc.ankr.com/eth',
    'base': 'https://rpc.ankr.com/base',
    'arbitrum': 'https://rpc.ankr.com/arbitrum',
    'scroll': 'https://rpc.scroll.io',
    'zksync': 'https://rpc.ankr.com/zksync_era',
    'optimism': 'https://rpc.ankr.com/optimism'
}

CHAINS_DATA = {
    'ethereum': {'explorer': 'https://etherscan.io/tx/'},
    'base': {'explorer': 'https://basescan.org/tx/'},
    'arbitrum': {'explorer': 'https://arbiscan.io/tx/'},
    'zksync': {'explorer': 'https://explorer.zksync.io/tx/'},
    'optimism': {'explorer': 'https://optimistic.etherscan.io/tx/'},
    'scroll': {'explorer': 'https://scrollscan.com/tx/'},
    'nova': {'explorer': 'https://nova-explorer.arbitrum.io/tx/'},
}

RHINO_CONTRACTS = {
    'base': '0x2f59e9086ec8130e21bd052065a9e6b2497bb102',
    'zksync': '0x1fa66e2B38d0cC496ec51F81c3e05E6A6708986F',
    'arbitrum': '0x10417734001162Ea139e8b044DFe28DbB8B28ad0',
    'bsc': '0xB80A582fa430645A043bB4f6135321ee01005fEf',
    'polygon': '0xba4eee20f434bc3908a0b18da496348657133a7e',
    'optimism': '0x0bCa65bf4b4c8803d2f0B49353ed57CAAF3d66Dc',
    'linea': '0xcF68a2721394dcf5dCF66F6265C1819720F24528',
    'nova': '0x0bCa65bf4b4c8803d2f0B49353ed57CAAF3d66Dc',
}
##############################################################

# будет рандомно брать dapp для Colateral и ликвидности ['layerbank'] (пока только один)
MASSIV_DAPP_POOL = ['layerbank']

##############################################################################
#########                    для свапов                #######################
##############################################################################

# только usdc
MASSIV_STABLE = ['USDC']

# будет рандомно брать dapp для свапа из этого массива ['Syncswap', 'Skydrome', 'Ambient', 'Izumi']
MASSIV_DAPP = ['Syncswap', 'Skydrome', 'Izumi']#Ambient - временно не воркает

# минималка ETH на кошельке, меньше 0.001 не рекомендую ставить
MIN_ETH_ON_WALLET = 0.001

# если рандом, то будет брать любое направление, процент и площадку [True или False]
RANDOM_SWAP = True

# если рандом, то процент будет брать из этого диапазона
PROCENT_SWAP_MIN = 75
PROCENT_SWAP_MAX = 90
