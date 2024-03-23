from termcolor import cprint
from modules.bridge_off_most import of_most_main
from modules.dmail_main import dmail_main
from loguru import logger
from config import RANDOM_SWAP
from sys import stderr
from modules.swap_main import swap_main, pool_main, colateral_main
from modules.volume import main_eth

logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <3}</level> | <level>{message}</level>")

if __name__ == '__main__':
    while True:
        print('Выбери действие: ')
        print('1. Официальный мост')
        print('2. Свапы')
        print('3. Dmail')
        print('4. Ликвидность Aave')
        print('5. Переключатель (Collateral) Aave')
        print('6. Wrap/Unwrap ETH')
        print('7. Объемы ETH okx -> lending')

        cprint('0. Закончить работу', 'red')
        nomer = int(input('Номер действия: '))

        if nomer == 1:
            procent_min = int(input('min % ETH для бриджа: '))
            procent_max = int(input('max % ETH для бриджа: '))

            parametrs = {
                'procent_min': procent_min,
                'procent_max': procent_max,
                'current_account': 0,
                'max_acconts': 0,

            }

            of_most_main(2, parametrs)

        elif nomer == 2:

            count_min = int(input('min кол-во транзакций: '))
            count_max = int(input('max кол-во транзакций: '))
            nomer_puti = 0

            if not RANDOM_SWAP:
                print('Выбери направление: ')
                print('1. В USDC')
                print('2. В ETH')
                nomer_puti = int(input('Номер направления: '))

                procent_min = int(input('min % монеты для свапа: '))
                procent_max = int(input('max % монеты для свапа: '))

            parametrs = {
                'procent_min': procent_min if nomer_puti!= 0 else 0,
                'procent_max': procent_max if nomer_puti!= 0 else 0,
                'count_min': count_min,
                'count_max': count_max,
            }
            swap_main(nomer_puti, parametrs)

        elif nomer == 3:

            count_min = int(input('min кол-во писем: '))
            count_max = int(input('max кол-во писем: '))

            parametrs = {
                'count_min': count_min,
                'count_max': count_max,
            }

            dmail_main(parametrs)

        elif nomer == 4:

            marshrut = int(input('1. Вносим\n2. Забираем \n'))

            procent_min = int(input('min % ETH для действия: '))
            procent_max = int(input('max % ETH для действия: '))

            parametrs = {
                'marshrut': marshrut,
                'procent_min': procent_min,
                'procent_max': procent_max,
            }

            pool_main(parametrs)

        elif nomer == 5:

            count_min = int(input('min кол-во: '))
            count_max = int(input('max кол-во: '))

            parametrs = {
                'count_min': count_min,
                'count_max': count_max,
            }

            colateral_main(parametrs)

        elif nomer == 6:
            wrap_check = int(input('Wrap = 1, Unwrap = 2, случайные врапы = 3 '))
            procent_min = int(input('min % ETH для wrap/unwrap: '))
            procent_max = int(input('max % ETH для wrap/unwrap: '))

            if wrap_check == 3:
                count_min = int(input('min кол-во: '))
                count_max = int(input('max кол-во: '))

            parametrs = {
                'procent_min': procent_min,
                'procent_max': procent_max,
                'current_account': 0,
                'max_acconts': 0,
                'wrap_check': wrap_check,
                'count_min': count_min if wrap_check == 3 else 0,
                'count_max': count_max if wrap_check == 3 else 0,
            }

            if parametrs['wrap_check'] == 3:
                swap_main(0, parametrs)
            else:
                of_most_main(1, parametrs)

        elif nomer == 7:

            main_eth()

        else:
            break

    print("Скрипт закончил работу!!!")
