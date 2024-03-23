from web3 import Web3
from openpyxl import Workbook
import asyncio
from web3 import Web3
from openpyxl import Workbook

from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.models import StarknetChainId
from starknet_py.net.signer.stark_curve_signer import KeyPair

w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/zksync_era'))

def balance_check(wallet):
    try:
        address = w3.to_checksum_address(wallet)
        balance_native = w3.eth.get_balance(address) / 10 ** 18
        nonce = w3.eth.get_transaction_count(address)  # исправлено на getTransactionCount
        return address, round(balance_native, 5), nonce
    except:
        raise ValueError(f'Ошибка при получении информации по аккаунту {acc}')

def main_Zk():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(['address', 'balance', 'tx count'])
    sheet.column_dimensions['A'].width = 65
    sheet.column_dimensions['B'].width = 12
    sheet.column_dimensions['C'].width = 10

    with open('wallets.txt', 'r') as keys_file:
        wallets = [line.replace("\n", "") for line in keys_file.readlines()]

    print(f'Загружено {len(wallets)} кошельков ZkSync')
    print(f'Проверяем....')

    for wallet in wallets:
        try:
            address, balance_native, nonce = balance_check(wallet)
            sheet.append([address, balance_native, nonce])
        except Exception as error:
            print(error)
            sheet.append(["Неверный адрес аккаунта", "N/A", "N/A"])
    print('Данные сохранены в balances_zk.xlsx')
    workbook.save("balances_zk.xlsx")

async def check_stark(str_address, str_pk):
    key_pair = KeyPair.from_private_key(eval(str_pk))
    account = Account(
        address=eval(str_address),
        client=FullNodeClient(node_url='https://starknet-mainnet.public.blastapi.io'),
        key_pair=key_pair,
        chain=StarknetChainId.MAINNET,
    )
    bal = await account.get_balance()
    tx = await account.get_nonce()
    return Web3.from_wei(bal, 'ether'), tx

async def main():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(['address', 'balance', 'tx count'])
    sheet.column_dimensions['A'].width = 65
    sheet.column_dimensions['B'].width = 12
    sheet.column_dimensions['C'].width = 10

    with open('wallets_stark.txt', 'r') as wal_f:
        wal_lst = [line.replace("\n", "") for line in wal_f.readlines()]
    with open('keys_stark.txt', 'r') as key_f:
        key_lst = [line.replace("\n", "") for line in key_f.readlines()]
    if len(wal_lst) != len(key_lst):
        print('Количество адресов и приватников разное!!!')
        exit()
    wal_data = list(zip(wal_lst, key_lst))
    print(f'Загружено {len(wal_lst)} кошельков Starknet')
    print(f'Проверяем....')
    for address, key in wal_data:
        try:
            native_balance, tx_count = await check_stark(address, key)
            sheet.append([address, native_balance, tx_count])
        except Exception as e:
            print(e)
            sheet.append([address, 0, 0])
            pass
    print('Данные сохранены в balance_stark.xlsx')
    workbook.save('balance_stark.xlsx')


def main_Stark():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

if __name__ == "__main__":

    while True:
        message = """
***********************************************
Смотрим статистику в: 

1. ZkSync
2. StarkNet
0. Выход
        """
        print(message)
        number = int(input("Номер: "))
        if number == 1:
            main_Zk()
        elif number == 2:
            main_Stark()
        else:
            break

