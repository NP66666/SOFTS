SHUFFLE_WALLETS = False # True | False - перемешивать ли кошельки

RETRY = 3 # кол-во попыток при ошибках / фейлах

TIME_SLEEP = [50, 100] #время между акками

TIME_SLEEP_FOR_CIRCLE = [50, 100] #время между кругами

MAX_GWEI = 60

GWEI_MULTIPLIER = 1.1 # умножать текущий гвей на 1.1 | для случаев если газ резко вырастает и транза зависает на долго

RPCS = {
    'ethereum': 'https://rpc.ankr.com/eth',
    'arbitrum': 'https://rpc.ankr.com/arbitrum',
    'optimism': 'https://optimism.llamarpc.com',
    'base':     'https://base.publicnode.com',
    'linea':    'https://rpc.linea.build',
    'kava':     'https://evm.kava.io'
}

USE_WITHDROW_FROM_OKX = True# если включено, будет выводить с окекса и пополнять через меркли KAVA
OKX_WITHDRAW_VALUES = {
    'arbitrum': [0.002, 0.003], # вывести в Arbitrum  ETH
    'base': [0.003, 0.004],
}

#количество кругов arbitrum<->base
CYCLE_COUNT = [2, 2]
#сумма бриджа
BRIDGE_VOLUME = [0.5, 0.53] #ВНИМАНИЕ! Максимальная сумма не больше минимальной суммы вывода!

#сколько оставлять в сети
USE_WITHDROW_FROM_WALLET = True# если включено, будет подчищать сети
BALANCE_VALUES = {
    'arbitrum': [0.0005, 0.001],
    'base': [0.0005, 0.001],
    #'kava': [0.1, 0.3]
}

# --------------------------------------------------------------------------------------------------

OKX_KEY = ""
OKX_SECRET = ""
OKX_PASSWORD = ""

# ---------------------------------------------------------------------------------------------------

BITGET_KEY = ""
BITGET_SECRET = ""
BITGET_PASSWORD = ""

BITGET_WITHDRAW_VALUES = {
    'arbitrum': [2000, 2100], # вывести в Arbitrum STG
}

BRIDGE_VOLUME_STG = [1950, 2000]

CYCLE_COUNT_STG = [4, 4] #сколько кругов kava<->base + три транзакции идет вспомогательных
