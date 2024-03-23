from modules.helper import get_tx_data, sing_and_chek_tx_legasy
from loguru import logger
from web3 import Web3
from modules.abi_and_contract import DEPLOYER_ABI, DEPLOYER_BYTECODE


def deploy_contract(chain_w3, account, parametrs):
    logger.info(f'[{parametrs["current_account"]}][{account.address}] Deploying contract')

    address = Web3.to_checksum_address(account.address)

    tx_data = get_tx_data(address, chain_w3)

    contract = chain_w3.eth.contract(
        abi=DEPLOYER_ABI,
        bytecode=DEPLOYER_BYTECODE
    )

    txn_data = contract.constructor().build_transaction(
        tx_data
    )

    txn_data.update({"gas": int(chain_w3.eth.estimate_gas(txn_data) * 1.3)})
    success_tx, txn_hash = sing_and_chek_tx_legasy(chain_w3, txn_data, account)
    if success_tx:
        logger.info(f"https://scrollscan.com/tx/{txn_hash.hex()}")
        logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                       f'[{address} Contract successfully deployed!')
    else:
        logger.error(f'[{address}] Deploy error')
