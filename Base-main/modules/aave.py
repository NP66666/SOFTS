import random

from loguru import logger
from web3 import Web3
from modules.abi_and_contract import AAVE_WETH_CONTRACT, AAVE_ABI, AAVE_CONTRACT, stable_abi, COLATERAL_AAVE_ABI
from modules.helper import sing_and_chek_tx, approve, get_tx_data, retry
from config import MIN_ETH_ON_WALLET, WITHDRAW_LEFT


@retry
def pool_aave(dapp, chain_w3, account, parametrs, procent):
    try:
        if parametrs['marshrut'] == 1:
            deposit(dapp, chain_w3, account, parametrs, procent)
        else:
            withdraw(dapp, chain_w3, account, parametrs, procent)
    except Exception as err:
        logger.error(f'[{account.address}][{dapp}] error: {type(err).__name__} {err}')


@retry
def colateral_aave(dapp, chain_w3, account, parametrs):
    try:
        contract = chain_w3.eth.contract(address=Web3.to_checksum_address('0xA238Dd80C259a72e81d7e4664a9801593F98d1c5'),
                                         abi=COLATERAL_AAVE_ABI)
        enabled = contract.functions.getUserEMode(
            account.address
        ).call()
        if enabled == 1:
            disable_collateral(dapp, chain_w3, account, parametrs)
        else:
            enable_collateral(dapp, chain_w3, account, parametrs)
    except Exception as err:
        logger.error(f'[{account.address}][{dapp}] error: {type(err).__name__} {err}')


@retry
def get_deposit_amount(chain_w3, address):
    weth_contract = chain_w3.eth.contract(address=AAVE_WETH_CONTRACT, abi=stable_abi)

    amount = weth_contract.functions.balanceOf(address).call()

    return amount


@retry
def deposit(dapp, chain_w3, account, parametrs, procent, volume=None):
    if not volume:
        amount = ((float(chain_w3.from_wei(chain_w3.eth.get_balance(account.address), "ether"))) * procent / 100) - MIN_ETH_ON_WALLET
        amount_wei = Web3.to_wei(amount, 'ether')
    else:
        amount_wei = procent
        amount = Web3.from_wei(amount_wei, 'ether')

    logger.info(
        f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{account.address}] Make deposit on Aave | {amount} ETH')

    contract = chain_w3.eth.contract(address=Web3.to_checksum_address(AAVE_CONTRACT), abi=AAVE_ABI)
    address = account.address

    tx_data = get_tx_data(address, chain_w3, amount_wei)

    txn_data = contract.functions.depositETH(
        chain_w3.to_checksum_address("0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"),
        address,
        0
    ).build_transaction(tx_data)

    estimated_gas = int(chain_w3.eth.estimate_gas(txn_data) * 1.2)
    txn_data['gas'] = estimated_gas

    success_tx, txn_hash = sing_and_chek_tx(chain_w3, txn_data, account)
    if success_tx:
        logger.info(f"https://basescan.org/tx/{txn_hash.hex()}")
        logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                       f'[{address}][{dapp}] Successfully deposit')
    else:
        logger.error(f'[{address}][{dapp}] deposit error')


@retry
def withdraw(dapp, chain_w3, account, parametrs, procent=None, leave_balance=None):
    address = Web3.to_checksum_address(account.address)
    contract = chain_w3.eth.contract(address=Web3.to_checksum_address(AAVE_CONTRACT), abi=AAVE_ABI)
    amount = int(get_deposit_amount(chain_w3, address))
    if procent:
        amount = int(amount * procent / 100)

    if leave_balance:
        amount = int(amount - Web3.to_wei(round(random.uniform(*WITHDRAW_LEFT), 5), 'ether'))

    if amount > 0:

        logger.info(
            f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{account.address}] Make withdraw from Aave | ' +
            f'{Web3.from_wei(amount, "ether")} ETH')

        approve(chain_w3, amount, "0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7", AAVE_CONTRACT, account)

        tx_data = get_tx_data(address, chain_w3)

        txn_data = contract.functions.withdrawETH(
            chain_w3.to_checksum_address("0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"),
            amount,
            address
        ).build_transaction(tx_data)

        estimated_gas = int(chain_w3.eth.estimate_gas(txn_data) * 1.2)
        txn_data['gas'] = estimated_gas

        success_tx, swap_txn_hash = sing_and_chek_tx(chain_w3, txn_data, account)
        if success_tx:
            logger.info(f"https://basescan.org/tx/{swap_txn_hash.hex()}")
            logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                           f'[{address}][{dapp}] Successfully withdraw')
        else:
            logger.error(f'[{address}][{dapp}] withdraw error')
    else:
        logger.error(
            f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{account.address}] Deposit не найден')


@retry
def disable_collateral(dapp, chain_w3, account, parametrs):
    logger.info(
        f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{account.address}] Disable collateral on Aave')

    contract = chain_w3.eth.contract(address=Web3.to_checksum_address('0xA238Dd80C259a72e81d7e4664a9801593F98d1c5'),
                                     abi=COLATERAL_AAVE_ABI)
    address = account.address

    tx_data = get_tx_data(address, chain_w3)

    swap_txn = contract.functions.setUserEMode(
        0,
    ).build_transaction(tx_data)

    estimated_gas = int(chain_w3.eth.estimate_gas(swap_txn) * 1.2)
    swap_txn['gas'] = estimated_gas

    success_tx, swap_txn_hash = sing_and_chek_tx(chain_w3, swap_txn, account)
    if success_tx:
        logger.info(f"https://basescan.org/tx/{swap_txn_hash.hex()}")
        logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                       f'[{address}][{dapp}] Successfully disable')
    else:
        logger.error(f'[{address}][{dapp}] disable error')


@retry
def enable_collateral(dapp, chain_w3, account, parametrs):
    logger.info(
        f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{account.address}] Enable collateral on Aave')

    contract = chain_w3.eth.contract(address=Web3.to_checksum_address('0xA238Dd80C259a72e81d7e4664a9801593F98d1c5'),
                                     abi=COLATERAL_AAVE_ABI)
    address = account.address

    tx_data = get_tx_data(address, chain_w3)

    swap_txn = contract.functions.setUserEMode(
        1,
    ).build_transaction(tx_data)

    estimated_gas = int(chain_w3.eth.estimate_gas(swap_txn) * 1.2)
    swap_txn['gas'] = estimated_gas

    success_tx, swap_txn_hash = sing_and_chek_tx(chain_w3, swap_txn, account)
    if success_tx:
        logger.info(f"https://basescan.org/tx/{swap_txn_hash.hex()}")
        logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                       f'[{address}][{dapp}] Successfully enable')
    else:
        logger.error(f'[{address}][{dapp}] enable error')
