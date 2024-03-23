from loguru import logger
from web3 import Web3
from modules.abi_and_contract import LAYERBANK_WETH_CONTRACT, layerbank_abi, LAYERBANK_CONTRACT, stable_abi
from modules.helper import sing_and_chek_tx_legasy, approve


def pool_layerbank(dapp, chain_w3, account, parametrs, procent):
    try:
        if parametrs['marshrut'] == 1:
            deposit(dapp, chain_w3, account, parametrs, procent)
        else:
            withdraw(dapp, chain_w3, account, parametrs, procent)
    except Exception as err:
        logger.error(f'[{account.address}][{dapp}] error: {type(err).__name__} {err}')


def colateral_layerbank(dapp, chain_w3, account, parametrs):
    try:
        contract = chain_w3.eth.contract(address=Web3.to_checksum_address(LAYERBANK_CONTRACT), abi=layerbank_abi)
        enabled = contract.functions.usersOfMarket(
            LAYERBANK_WETH_CONTRACT,
            account.address
        ).call()
        if enabled == 1:
            disable_collateral(dapp, chain_w3, account, parametrs)
        else:
            enable_collateral(dapp, chain_w3, account, parametrs)
    except Exception as err:
        logger.error(f'[{account.address}][{dapp}] error: {type(err).__name__} {err}')


def get_deposit_amount(chain_w3, address):
    weth_contract = chain_w3.eth.contract(address=LAYERBANK_WETH_CONTRACT, abi=stable_abi)
    amount = weth_contract.functions.balanceOf(address).call()
    return amount


def deposit(dapp, chain_w3, account, parametrs, procent):
    amount = (float(chain_w3.from_wei(chain_w3.eth.get_balance(account.address), "ether"))) * procent / 100
    amount_wei = Web3.to_wei(amount, 'ether')
    logger.info(
        f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{account.address}] Make deposit on LayerBank | {amount} ETH')

    contract = chain_w3.eth.contract(address=Web3.to_checksum_address(LAYERBANK_CONTRACT), abi=layerbank_abi)
    address = account.address

    txn_data = contract.functions.supply(
        chain_w3.to_checksum_address(LAYERBANK_WETH_CONTRACT),
        amount_wei
    ).build_transaction({
        "chainId": chain_w3.eth.chain_id,
        "from": address,
        "gasPrice": chain_w3.eth.gas_price,
        "nonce": chain_w3.eth.get_transaction_count(address),
        "value": amount_wei
    })

    txn_data.update({"gas": int(chain_w3.eth.estimate_gas(txn_data) * 1.3)})
    success_tx, txn_hash = sing_and_chek_tx_legasy(chain_w3, txn_data, account)
    if success_tx:
        logger.info(f"https://scrollscan.com/tx/{txn_hash.hex()}")
        logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                       f'[{address}][{dapp}] Successfully deposit')
    else:
        logger.error(f'[{address}][{dapp}] deposit error')


def withdraw(dapp, chain_w3, account, parametrs, procent):
    address = Web3.to_checksum_address(account.address)
    contract = chain_w3.eth.contract(address=Web3.to_checksum_address(LAYERBANK_CONTRACT), abi=layerbank_abi)

    amount = int(get_deposit_amount(chain_w3, address) * procent / 100)

    if amount > 0:
        logger.info(
            f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{account.address}] Make withdraw from LayerBank | ' +
            f'{Web3.from_wei(amount, "ether")} ETH')

        approve(chain_w3, amount, LAYERBANK_WETH_CONTRACT, LAYERBANK_CONTRACT, account)

        swap_txn = {
            "chainId": chain_w3.eth.chain_id,
            "from": address,
            "gasPrice": chain_w3.eth.gas_price,
            "nonce": chain_w3.eth.get_transaction_count(address),
        }
        swap_txn = contract.functions.redeemUnderlying(
            chain_w3.to_checksum_address(LAYERBANK_WETH_CONTRACT),
            amount
        ).build_transaction(swap_txn)

        swap_txn.update({"gas": int(chain_w3.eth.estimate_gas(swap_txn) * 1.3)})
        success_tx, swap_txn_hash = sing_and_chek_tx_legasy(chain_w3, swap_txn, account)
        if success_tx:
            logger.info(f"https://scrollscan.com/tx/{swap_txn_hash.hex()}")
            logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                           f'[{address}][{dapp}] Successfully withdraw')
        else:
            logger.error(f'[{address}][{dapp}] withdraw error')
    else:
        logger.error(
            f'[{parametrs["current_account"]}]/{parametrs["max_acconts"]}][{account.address}] Deposit не найден')


def disable_collateral(dapp, chain_w3, account, parametrs):
    logger.info(
        f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{account.address}] Disable collateral on LayerBank')

    contract = chain_w3.eth.contract(address=Web3.to_checksum_address(LAYERBANK_CONTRACT), abi=layerbank_abi)
    address = account.address
    swap_txn = {
        "chainId": chain_w3.eth.chain_id,
        "from": address,
        "gasPrice": chain_w3.eth.gas_price,
        "nonce": chain_w3.eth.get_transaction_count(address),
    }

    swap_txn = contract.functions.enterMarkets([Web3.to_checksum_address(LAYERBANK_WETH_CONTRACT)]).build_transaction(
        swap_txn)

    swap_txn.update({"gas": int(chain_w3.eth.estimate_gas(swap_txn) * 1.3)})
    success_tx, swap_txn_hash = sing_and_chek_tx_legasy(chain_w3, swap_txn, account)
    if success_tx:
        logger.info(f"https://scrollscan.com/tx/{swap_txn_hash.hex()}")
        logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                       f'[{address}][{dapp}] Successfully disable')
    else:
        logger.error(f'[{address}][{dapp}] disable error')


def enable_collateral(dapp, chain_w3, account, parametrs):
    logger.info(
        f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{account.address}] Enable collateral on LayerBank')

    contract = chain_w3.eth.contract(address=Web3.to_checksum_address(LAYERBANK_CONTRACT), abi=layerbank_abi)
    address = account.address
    swap_txn = {
        "chainId": chain_w3.eth.chain_id,
        "from": address,
        "gasPrice": chain_w3.eth.gas_price,
        "nonce": chain_w3.eth.get_transaction_count(address),
    }

    swap_txn = contract.functions.enterMarkets([Web3.to_checksum_address(LAYERBANK_WETH_CONTRACT)]).build_transaction(
        swap_txn)

    swap_txn.update({"gas": int(chain_w3.eth.estimate_gas(swap_txn) * 1.3)})
    success_tx, swap_txn_hash = sing_and_chek_tx_legasy(chain_w3, swap_txn, account)
    if success_tx:
        logger.info(f"https://scrollscan.com/tx/{swap_txn_hash.hex()}")
        logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                       f'[{address}][{dapp}] Successfully enable')
    else:
        logger.error(f'[{address}][{dapp}] enable error')
