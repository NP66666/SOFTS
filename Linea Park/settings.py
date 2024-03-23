
SHUFFLE_WALLETS = True                      # True | False - перемешивать ли кошельки
RETRY = 3                                   # кол-во попыток при ошибках / фейлах

ETH_MAX_GWEI = 60
LINEA_MAX_GWEI = 1.8
TO_WAIT_TX = 3                              # сколько минут ожидать транзакцию. если транза будет находится в пендинге после указанного времени то будет считатся зафейленной

RPCS = {
    'ethereum': 'https://rpc.ankr.com/eth',
    'linea': 'https://linea.drpc.org',
}

MIN_LINEA_BALANCE = 0.0004                  # минимальный баланс 0.0004 ETH (~1.5$). проверяется перед каждым модулем, если баланс ниже - выводит с OKX
OKX_WITHDRAW_VALUES = [0.001, 0.002]        # выводить с OKX от 0.001 до 0.002 ETH в Linea

SLEEP_AFTER_TX = [20, 40]                   # задержка после каждой транзы 10-20 секунд

LINEA_QUESTS = {                            # список квестов для выполнения | True - False
    # week 1
    'Gamerboom': True,                      # https://layer3.xyz/quests/linea-gamerboom

    # week 2
    'Yooldo': True,                         # https://layer3.xyz/quests/linea-yooldo
    'SatoshiUniverse': True,                # https://layer3.xyz/quests/linea-satoshi-universe
    'Pictograph': True,                     # https://layer3.xyz/quests/linea-pictograph
    'Abyss': True,                          # https://layer3.xyz/quests/linea-abyss-world

    # week 3
    'Dmail': True,                          # https://layer3.xyz/quests/linea-dmail
    'Gamic': True,                          # https://layer3.xyz/quests/linea-gamic-app
    'BitAvatar': True,                      # https://layer3.xyz/quests/linea-bitavatar
    'ReadOn': True,                         # https://layer3.xyz/quests/linea-readon
    'SendingMe': True,                      # https://layer3.xyz/quests/linea-sending-me
    'AsMatch': True,                        # https://layer3.xyz/quests/linea-asmatch | !NEW!
    'SocialScan': True,                        # https://layer3.xyz/quests/linea-socialscan | !NEW!

    # week 4
    'Timeless': True,                       # https://layer3.xyz/quests/linea-timeless-wallet
    'Zypher': True,                         # https://layer3.xyz/quests/2048-zypher | !NEW!
    'Yuliverse': True,                      # https://layer3.xyz/quests/linea-yuliverse | !NEW!
    'YooldoRPD': True,                      # https://layer3.xyz/quests/yooldo-rpd | !NEW!

    # week 5
    'Battlemon': True,                      # https://layer3.xyz/quests/linea-battlemon | !NEW!
    'Brototype': True,                      # https://layer3.xyz/quests/linea-brototype | !NEW!
}

SENDING_ME_AMOUNT = [0.00000100, 0.00000100]    # отправлять от 0.00000100 до 0.00000100 ETH (стандартное значение) - округление до 8 знаков после запятой

# -------------------------------------------

OKX_API_KEY = ''
OKX_API_SECRET = ''
OKX_API_PASSWORD = ''

TG_BOT_TOKEN = ''                           # токен от тг бота (`12345:Abcde`) для уведомлений. если не нужно - оставляй пустым
TG_USER_ID = []                             # тг айди куда должны приходить уведомления. [21957123] - для отправления уведомления только себе, [21957123, 103514123] - отправлять нескольким людями
