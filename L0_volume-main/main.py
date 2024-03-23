import random
import time

from modules.utils import sleeping, logger
from modules.wallet import Wallet
from modules.stargate import Stargate
from modules.merkly import merkly_refuel
import settings


with open('keys.txt', 'r') as file:
    ACCOUNTS = [line.strip() for line in file]

with open('recipients.txt', 'r') as file:
    WITHDRAW = [line.strip() for line in file]

with open('recipients_OKX.txt', 'r') as file:
    WITHDRAW2 = [line.strip() for line in file]

WITHDRAW_ACC = {}
if len(WITHDRAW) == len(ACCOUNTS):
    wal_data = list(zip(WITHDRAW, ACCOUNTS))
    for address, acc in wal_data:
        WITHDRAW_ACC[acc] = address

WITHDRAW_ACC2 = {}
if len(WITHDRAW2) == len(ACCOUNTS):
    wal_data = list(zip(WITHDRAW2, ACCOUNTS))
    for address, acc in wal_data:
        WITHDRAW_ACC2[acc] = address


def main_eth():
    if len(WITHDRAW) != len(ACCOUNTS):
        print('Количество кошельков вывода и приватников разное!!! Отменяем вывод')
        return

    if settings.SHUFFLE_WALLETS:
        random.shuffle(ACCOUNTS)

    max_acconts = len(ACCOUNTS)
    print(f'Загружено {len(ACCOUNTS)} кошельков')

    for current_account, account in enumerate(ACCOUNTS):

        recipients = WITHDRAW_ACC[account]
        try:
            wallet = Wallet(account, recipients, recipients)

            wallet.okx_withdraw(chain='arbitrum')

            total_cycles = random.randint(settings.CYCLE_COUNT[0], settings.CYCLE_COUNT[1])

            logger.info(f"[{current_account+1}/{max_acconts}][{wallet.address}] начал работу. Всего кругов - {total_cycles}")

            for number in range(total_cycles):
                logger.info(f"Круг [{number + 1}/{total_cycles}]")

                Stargate(wallet, 'arbitrum', 'base', 1)
                Stargate(wallet, 'base', 'arbitrum', 1)

                sleeping(*settings.TIME_SLEEP_FOR_CIRCLE)

            logger.info(f"[{current_account + 1}/{max_acconts}][{wallet.address}] закончил работу с объемами")
            wallet.send_to('arbitrum')
        except Exception as e:
            logger.error(f"Ошибка: {e}")

        sleeping(*settings.TIME_SLEEP)


def main_stg():
    if len(WITHDRAW) != len(ACCOUNTS):
        print('Количество кошельков вывода и приватников разное!!! Отменяем вывод')
        return

    if settings.SHUFFLE_WALLETS:
        random.shuffle(ACCOUNTS)

    max_acconts = len(ACCOUNTS)
    print(f'Загружено {len(ACCOUNTS)} кошельков')

    for current_account, account in enumerate(ACCOUNTS):

        recipients = WITHDRAW_ACC[account]
        recipients2 = WITHDRAW_ACC2[account]
        try:
            wallet = Wallet(account, recipients, recipients2)
            logger.info(f"[{current_account + 1}/{max_acconts}][{wallet.address}] начал работу")

            wallet.bitget_withdraw(chain='arbitrum', SYMBOL='STG')

            if settings.USE_WITHDROW_FROM_OKX:
                wallet.okx_withdraw(chain='arbitrum')
                wallet.okx_withdraw(chain='base')
                merkly_refuel("arbitrum", "kava", 0.8, 0.85, wallet.privatekey)
                time.sleep(15)
                merkly_refuel("arbitrum", "kava", 0.8, 0.85, wallet.privatekey)
                time.sleep(15)

            Stargate(wallet, 'arbitrum', 'kava', 2)

            total_cycles = random.randint(settings.CYCLE_COUNT_STG[0], settings.CYCLE_COUNT_STG[1])
            logger.info(f"Всего кругов - {total_cycles}")

            for number in range(total_cycles):
                logger.info(f"Круг [{number + 1}/{total_cycles}]")

                Stargate(wallet, 'kava', 'base', 2)
                Stargate(wallet, 'base', 'kava', 2, True if (number+1==total_cycles) else False)

                sleeping(*settings.TIME_SLEEP_FOR_CIRCLE)

            Stargate(wallet, 'kava', 'base', 2, True)
            Stargate(wallet, 'base', 'arbitrum', 2, True)

            logger.info(f"[{current_account + 1}/{max_acconts}][{wallet.address}] закончил работу с объемами")

            wallet.send_to_STG('arbitrum')
            if settings.USE_WITHDROW_FROM_WALLET:
                wallet.send_to('arbitrum')
                wallet.send_to('base')
                #wallet.send_to('kava')
        except Exception as e:
            logger.error(f"Ошибка: {e}")

        sleeping(*settings.TIME_SLEEP)


if __name__ == '__main__':
    print(f"""1. STARGATE | ARB<->BASE | ETH | OKX 
2. STARGATE | BASE <-> KAVA | STG | BITGET 
""")

    route = int(input("Маршрут: "))

    if route == 1:
        main_eth()
    else:
        main_stg()

    print("Скрипт закончил работу!!!")
