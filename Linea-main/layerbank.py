from loguru import logger
from web3 import Web3
from abi_and_contract import layerbank_contract, layerbank_abi, layerbank_price_contract, layerbank_price_abi
from helper import sing_and_chek_tx_legasy


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
        contract = chain_w3.eth.contract(address=Web3.to_checksum_address(layerbank_contract), abi=layerbank_abi)
        enabled = contract.functions.usersOfMarket(
        "0xc7D8489DaE3D2EbEF075b1dB2257E2c231C9D231",
        account.address
        ).call()
        if enabled == 1:
            disable_collateral(dapp, chain_w3, account, parametrs)
        else:
            enable_collateral(dapp, chain_w3, account, parametrs)
    except Exception as err:
        logger.error(f'[{account.address}][{dapp}] error: {type(err).__name__} {err}')


def get_deposit_amount(chain_w3, address):
    contract = chain_w3.eth.contract(address=Web3.to_checksum_address(layerbank_contract), abi=layerbank_abi)
    amount_usd = contract.functions.accountLiquidityOf(address).call()
    amount_usd = amount_usd[1]
    contract = chain_w3.eth.contract(address=Web3.to_checksum_address(layerbank_price_contract), abi=layerbank_price_abi)
    price_eth = contract.functions.priceOfETH().call()
    deposit = float(amount_usd/price_eth) * 995 / 1000
    deposit = chain_w3.to_wei(deposit, 'ether')
    return deposit


def deposit(dapp, chain_w3, account, parametrs, procent):
    amount = (float(chain_w3.from_wei(chain_w3.eth.get_balance(account.address), "ether"))) * procent / 100
    amount_wei = Web3.to_wei(amount, 'ether')
    logger.info(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}] Make deposit on LayerBank | {amount} ETH')

    contract = chain_w3.eth.contract(address=Web3.to_checksum_address(layerbank_contract), abi=layerbank_abi)
    address = account.address
    gToken_address = Web3.to_checksum_address("0xc7D8489DaE3D2EbEF075b1dB2257E2c231C9D231")

    txn_data = contract.functions.supply(
        gToken_address,
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
        logger.info(f"https://lineascan.build/tx/{txn_hash.hex()}")
        logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                       f'[{address}][{dapp}] Successfully deposit')
    else:
        logger.error(f'[{address}][{dapp}] deposit error')


def withdraw(dapp, chain_w3, account, parametrs, procent):
    address = Web3.to_checksum_address(account.address)
    contract = chain_w3.eth.contract(address=Web3.to_checksum_address(layerbank_contract), abi=layerbank_abi)
    gToken_address = Web3.to_checksum_address("0xc7D8489DaE3D2EbEF075b1dB2257E2c231C9D231")

    amount = int(get_deposit_amount(chain_w3, address)*procent/100)
    if amount > 0:
        logger.info(
            f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{account.address}] Make withdraw from LayerBank | ' +
            f'{Web3.from_wei(amount, "ether")} ETH')

        swap_txn = {
            "chainId": chain_w3.eth.chain_id,
            "from": address,
            "gasPrice": chain_w3.eth.gas_price,
            "nonce": chain_w3.eth.get_transaction_count(address),
        }
        swap_txn = contract.functions.redeemUnderlying(
            gToken_address,
            amount
        ).build_transaction(swap_txn)

        swap_txn.update({"gas": int(chain_w3.eth.estimate_gas(swap_txn) * 1.3)})
        success_tx, swap_txn_hash = sing_and_chek_tx_legasy(chain_w3, swap_txn, account)
        if success_tx:
            logger.info(f"https://lineascan.build/tx/{swap_txn_hash.hex()}")
            logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                           f'[{address}][{dapp}] Successfully withdraw')
        else:
            logger.error(f'[{address}][{dapp}] withdraw error')
    else:
        logger.error(f'[{parametrs["current_account"]}][{account.address}] Deposit не найден')


def disable_collateral(dapp, chain_w3, account, parametrs):

    logger.info(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{account.address}] Disable collateral on LayerBank')

    contract = chain_w3.eth.contract(address=Web3.to_checksum_address(layerbank_contract), abi=layerbank_abi)
    address = account.address
    swap_txn = {
        "chainId": chain_w3.eth.chain_id,
        "from": address,
        "gasPrice": chain_w3.eth.gas_price,
        "nonce": chain_w3.eth.get_transaction_count(address),
    }

    gTokens_address = "0xc7D8489DaE3D2EbEF075b1dB2257E2c231C9D231"
    swap_txn = contract.functions.enterMarkets([Web3.to_checksum_address(gTokens_address)]).build_transaction(swap_txn)

    swap_txn.update({"gas": int(chain_w3.eth.estimate_gas(swap_txn) * 1.3)})
    success_tx, swap_txn_hash = sing_and_chek_tx_legasy(chain_w3, swap_txn, account)
    if success_tx:
        logger.info(f"https://lineascan.build/tx/{swap_txn_hash.hex()}")
        logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                       f'[{address}][{dapp}] Successfully disable')
    else:
        logger.error(f'[{address}][{dapp}] disable error')


def enable_collateral(dapp, chain_w3, account, parametrs):

    logger.info(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{account.address}] Enable collateral on LayerBank')

    contract = chain_w3.eth.contract(address=Web3.to_checksum_address(layerbank_contract), abi=layerbank_abi)
    address = account.address
    swap_txn = {
        "chainId": chain_w3.eth.chain_id,
        "from": address,
        "gasPrice": chain_w3.eth.gas_price,
        "nonce": chain_w3.eth.get_transaction_count(address),
    }

    gTokens_address = "0xc7D8489DaE3D2EbEF075b1dB2257E2c231C9D231"
    swap_txn = contract.functions.enterMarkets([Web3.to_checksum_address(gTokens_address)]).build_transaction(swap_txn)


    swap_txn.update({"gas": int(chain_w3.eth.estimate_gas(swap_txn) * 1.3)})
    success_tx, swap_txn_hash = sing_and_chek_tx_legasy(chain_w3, swap_txn, account)
    if success_tx:
        logger.info(f"https://lineascan.build/tx/{swap_txn_hash.hex()}")
        logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                       f'[{address}][{dapp}] Successfully enable')
    else:
        logger.error(f'[{address}][{dapp}] enable error')
