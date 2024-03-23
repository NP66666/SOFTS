from loguru import logger
import random
from web3 import Web3
from web3.auto import w3
from helper import accounts, cheker_gwei, sleeping, sing_and_chek_tx
from abi_and_contract import of_most_from_Eth_abi

w3_eth = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))

of_most_from_Eth_adress = w3.to_checksum_address('0xd19d4B5d358258f05D7B411E21A1460D11B0876F')
of_most_from_Eth_contract = w3_eth.eth.contract(address=of_most_from_Eth_adress, abi=of_most_from_Eth_abi)


def of_most_main(nomer_puti, parametrs):
    current_account = 0
    max_accounts = len(accounts)
    parametrs['max_acconts'] = max_accounts

    for account in accounts:
        cheker_gwei()
        current_account += 1

        parametrs['current_account'] = current_account
        if nomer_puti == 2:
            off_most_to_Linea(account, parametrs)

        sleeping()  # время между аккаунтами


def off_most_to_Linea(account, parametrs):
    chain_w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))
    try:
        contract = of_most_from_Eth_contract
        address = chain_w3.to_checksum_address(account.address)

        value_int = chain_w3.eth.get_balance(address)
        procent = random.randint(parametrs['procent_min'], parametrs['procent_max'])
        value = chain_w3.from_wei(value_int * procent // 100, "ether")
        value_int = value_int * procent // 100

        fee = int(chain_w3.eth.gas_price * 10e4)

        swap_txn = contract.functions.sendMessage(
            address,
            fee,
            b""
        ).build_transaction({
            'from': address,
            'maxFeePerGas': int(chain_w3.eth.gas_price + chain_w3.eth.gas_price * 0.1),
            'maxPriorityFeePerGas': chain_w3.eth.gas_price,
            'value': value_int,
            'nonce': chain_w3.eth.get_transaction_count(address, 'pending'),
            'gas': 160000,
        })

        success_tx, swap_txn_hash = sing_and_chek_tx(chain_w3, swap_txn, account)
        if success_tx:
            logger.info(f"https://etherscan.io/tx/{swap_txn_hash.hex()}")
            logger.success(
                f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{address}]'
                f'Successfully bridge {round(value, 5)} ETH to [Linea]!')
        else:
            logger.error(f'[{account.address}] bridge error to [Linea]')
    except Exception as err:
        logger.error(f'[{account.address}] bridge error to [Linea]: {type(err).__name__} {err}')
