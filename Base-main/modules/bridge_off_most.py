from loguru import logger
import random
from web3 import Web3
from modules.helper import accounts, cheker_gwei, sleeping, sing_and_chek_tx, get_tx_data, USE_PROXY, PROXY_ACC
from modules.abi_and_contract import BASE_BRIDGE_CONTRACT, BASE_BRIDGE_ABI, WETH_ABI, BASE_TOKENS
from config import RPC_BASE


def of_most_main(nomer_puti, parametrs):
    chain_w3 = Web3(Web3.HTTPProvider(RPC_BASE))
    current_account = 0
    max_accounts = len(accounts)
    parametrs['max_acconts'] = max_accounts

    for account in accounts:
        cheker_gwei()
        current_account += 1

        parametrs['current_account'] = current_account
        if nomer_puti == 2:
            off_most_to_base(account, parametrs)
        elif nomer_puti == 1 and parametrs['wrap_check'] != 3:
            if USE_PROXY:
                proxy_list = PROXY_ACC[account.address].split(':')
                proxy = f'http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}'
                chain_w3 = Web3(
                    Web3.HTTPProvider(RPC_BASE, request_kwargs={"proxies": {'https': proxy, 'http': proxy}}))

            wrap(account, parametrs, chain_w3)

        sleeping()


def off_most_to_base(account, parametrs):
    chain_w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))

    try:
        contract = chain_w3.eth.contract(address=BASE_BRIDGE_CONTRACT, abi=BASE_BRIDGE_ABI)

        address = chain_w3.to_checksum_address(account.address)

        value_int = chain_w3.eth.get_balance(address)
        procent = random.randint(parametrs['procent_min'], parametrs['procent_max'])
        value = chain_w3.from_wei(value_int * procent // 100, "ether")
        value_int = value_int * procent // 100

        tx_data = get_tx_data(address, chain_w3, value_int)

        swap_txn = contract.functions.depositTransaction(
            address,
            value_int,
            100000,
            False,
            "0x01"
        ).build_transaction(tx_data)
        estimated_gas = int(chain_w3.eth.estimate_gas(swap_txn) * 1.2)
        swap_txn['gas'] = estimated_gas

        success_tx, swap_txn_hash = sing_and_chek_tx(chain_w3, swap_txn, account)
        if success_tx:
            logger.info(f"https://etherscan.io/tx/{swap_txn_hash.hex()}")
            logger.success(
                f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{address}]'
                f'Successfully bridge {round(value, 5)} ETH to [Base]!')
        else:
            logger.error(f'[{account.address}] bridge error to [Base]')
    except Exception as err:
        logger.error(f'[{account.address}] bridge error to [Base]: {type(err).__name__} {err}')


def wrap(account, parametrs, w3):
    chain_w3 = w3
    try:
        weth_contract = chain_w3.eth.contract(address=BASE_TOKENS["WETH"], abi=WETH_ABI)

        address = chain_w3.to_checksum_address(account.address)
        value_int = chain_w3.eth.get_balance(address)
        procent = random.randint(parametrs['procent_min'], parametrs['procent_max'])
        value = chain_w3.from_wei(value_int * procent // 100, "ether")
        value_int = value_int * procent // 100

        if parametrs['wrap_check'] == 1:
            tx_data = get_tx_data(address, chain_w3, value_int)
            swap_txn = weth_contract.functions.deposit().build_transaction(tx_data)
            parametrs['choice'] = 'Wrap'

        elif parametrs['wrap_check'] == 2:
            tx_data = get_tx_data(address, chain_w3)
            swap_txn = weth_contract.functions.withdraw(value_int).build_transaction(tx_data)
            parametrs['choice'] = 'Unwrap'

        elif parametrs['wrap_check'] == 3:

            if random.choice([True, False]):
                tx_data = get_tx_data(address, chain_w3, value_int)
                swap_txn = weth_contract.functions.deposit().build_transaction(tx_data)
                parametrs['choice'] = 'Wrap'

            else:
                tx_data = get_tx_data(address, chain_w3)
                swap_txn = weth_contract.functions.withdraw(value_int).build_transaction(tx_data)
                parametrs['choice'] = 'Unwrap'

        success_tx, swap_txn_hash = sing_and_chek_tx(chain_w3, swap_txn, account)

        if success_tx:
            logger.info(f"https://basescan.org/tx/{swap_txn_hash.hex()}")
            logger.success(
                f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{address}]'
                f'Successfully {parametrs["choice"]} {round(value, 5)} ETH!')
        else:
            logger.error(f'[{account.address}] {parametrs["choice"]} error ')

    except Exception as err:
        logger.error(f'[{account.address}] Wrap/Unwrap error: {type(err).__name__} {err}')
