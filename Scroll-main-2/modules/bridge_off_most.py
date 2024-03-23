from loguru import logger
import random
from web3 import Web3
from modules.helper import accounts, cheker_gwei, sleeping, sing_and_chek_tx, get_tx_data, sing_and_chek_tx_legasy, \
    USE_PROXY, PROXY_ACC
from modules.abi_and_contract import bridge_oracle_abi, bridge_deposit_abi, BRIDGE_CONTRACTS, SCROLL_TOKENS, WETH_ABI
from config import RPC_SCROLL
from web3.middleware import geth_poa_middleware


def of_most_main(nomer_puti, parametrs):
    chain_w3 = Web3(Web3.HTTPProvider(RPC_SCROLL))
    current_account = 0
    max_accounts = len(accounts)
    parametrs['max_acconts'] = max_accounts

    for account in accounts:
        cheker_gwei()
        current_account += 1
        parametrs['current_account'] = current_account

        if nomer_puti == 2:
            off_most_to_scroll(account, parametrs)
        elif nomer_puti == 1 and parametrs['wrap_check'] != 3:
            if USE_PROXY:
                proxy_list = PROXY_ACC[account.address].split(':')
                proxy = f'http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}'
                chain_w3 = Web3(
                    Web3.HTTPProvider(RPC_SCROLL, request_kwargs={"proxies": {'https': proxy, 'http': proxy}}))

            wrap(account, parametrs, chain_w3)

        sleeping()


def off_most_to_scroll(account, parametrs):
    chain_w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))

    try:
        contract = chain_w3.eth.contract(
            address=chain_w3.to_checksum_address(BRIDGE_CONTRACTS["deposit"]),
            abi=bridge_deposit_abi)

        contract_oracle = chain_w3.eth.contract(
            address=chain_w3.to_checksum_address(BRIDGE_CONTRACTS["oracle"]),
            abi=bridge_oracle_abi)

        fee = contract_oracle.functions.estimateCrossDomainMessageFee(168000).call()


        address = chain_w3.to_checksum_address(account.address)

        value_int = chain_w3.eth.get_balance(address)
        procent = random.randint(parametrs['procent_min'], parametrs['procent_max'])
        value = chain_w3.from_wei(value_int * procent // 100, "ether")
        value_int = value_int * procent // 100

        swap_txn = contract.functions.depositETH(
            value_int,
            168000,
        ).build_transaction({
            "chainId": 534352,
            'from': address,
            'value': value_int + fee,
            'nonce': chain_w3.eth.get_transaction_count(address),
            'gas': 0,
        })

        estimated_gas = contract.functions.depositETH(
            value_int,
            168000,
        ).estimate_gas({
            'from': address,
            'value': value_int + fee
        })

        swap_txn['gas'] = int(estimated_gas * 1.1)

        success_tx, swap_txn_hash = sing_and_chek_tx(chain_w3, swap_txn, account)
        if success_tx:
            logger.info(f"https://etherscan.io/tx/{swap_txn_hash.hex()}")
            logger.success(
                f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{address}]'
                f'Successfully bridge {round(value, 5)} ETH to [Scroll]!')
        else:
            logger.error(f'[{account.address}] bridge error to [Scroll]')
    except Exception as err:
        logger.error(f'[{account.address}] bridge error to [Scroll]: {type(err).__name__} {err}')


def wrap(account, parametrs, w3):
    chain_w3 = w3
    if geth_poa_middleware not in chain_w3.middleware_onion:
        chain_w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    try:
        weth_contract = chain_w3.eth.contract(address=SCROLL_TOKENS["WETH"], abi=WETH_ABI)

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

        success_tx, swap_txn_hash = sing_and_chek_tx_legasy(chain_w3, swap_txn, account)

        if success_tx:
            logger.info(f"https://scrollscan.com/tx/{swap_txn_hash.hex()}")
            logger.success(
                f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{address}]'
                f'Successfully {parametrs["choice"]} {round(value, 5)} ETH!')
        else:
            logger.error(f'[{account.address}] {parametrs["choice"]} error ')

    except Exception as err:
        logger.error(f'[{account.address}] Wrap/Unwrap error: {type(err).__name__} {err}')
