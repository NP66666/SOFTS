import random
from modules.helper import sleeping, logger
from modules.wallet import Wallet
import config
from web3 import Web3
from modules.aave import deposit, withdraw
from config import (USE_PROCENT, DEPOSIT_VALUES_PROCENT, DEPOSIT_WAIT, MIN_ETH_ON_WALLET, DEPOSIT_VALUES,
                    PAUSA_MIN, PAUSA_MAX, CYCLES_WAIT, USE_WITHDRAW_FROM_WALLET)


with open('keys.txt', 'r') as file:
    ACCOUNTS = [line.strip() for line in file]

with open('recipients.txt', 'r') as file:
    WITHDRAW = [line.strip() for line in file]


WITHDRAW_ACC = {}
if len(WITHDRAW) == len(ACCOUNTS):
    wal_data = list(zip(WITHDRAW, ACCOUNTS))
    for address, acc in wal_data:
        WITHDRAW_ACC[acc] = address

w3 = Web3(Web3.HTTPProvider(config.RPC_BASE))

def main_eth():
    if len(WITHDRAW) != len(ACCOUNTS):
        print('Количество кошельков вывода и приватников разное!!! Отменяем вывод')
        return

    if config.SHUFFLE_WALLET:
        random.shuffle(ACCOUNTS)

    max_acconts = len(ACCOUNTS)
    print(f'Загружено {len(ACCOUNTS)} кошельков')

    for current_account, account in enumerate(ACCOUNTS):

        recipients = WITHDRAW_ACC[account]
        try:
            wallet = Wallet(account, recipients)

            wallet.okx_withdraw(chain='base')

            total_cycles = random.randint(config.CYCLES_COUNT[0], config.CYCLES_COUNT[1])

            logger.info(f"[{current_account+1}/{max_acconts}][{wallet.address}] начал работу. Всего кругов - {total_cycles}")

            parametrs = {}
            parametrs['max_acconts'] = 1
            parametrs['current_account'] = 1

            for number in range(total_cycles):
                logger.info(f"Круг [{number + 1}/{total_cycles}]")

                dapp = random.choice(config.MASSIV_DAPP_POOL)

                if USE_PROCENT:
                    balance_wei = w3.eth.get_balance(wallet.address)
                    random_procent = random.randint(DEPOSIT_VALUES_PROCENT[0], DEPOSIT_VALUES_PROCENT[1])
                    amount_wei = int(balance_wei * random_procent / 100) - Web3.to_wei(MIN_ETH_ON_WALLET, 'ether')
                else:
                    amount_wei = Web3.to_wei(random.uniform(DEPOSIT_VALUES[0], DEPOSIT_VALUES[1]) - MIN_ETH_ON_WALLET, 'ether')

                deposit(dapp, w3, wallet.account, parametrs, amount_wei, True)

                sleeping(*DEPOSIT_WAIT)

                if number == total_cycles-1:
                    withdraw(dapp, w3, wallet.account, parametrs, 100, True)
                else:
                    withdraw(dapp, w3, wallet.account, parametrs, 100)

                sleeping(*CYCLES_WAIT)


            logger.info(f"[{current_account + 1}/{max_acconts}][{wallet.address}] закончил работу с объемами")
            if USE_WITHDRAW_FROM_WALLET:
                wallet.send_to('base')
        except Exception as e:
            logger.error(f"Ошибка: {e}")

        sleeping(PAUSA_MIN, PAUSA_MAX)
