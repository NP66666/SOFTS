from modules.helper import sing_and_chek_tx, allowance, create_value, get_tx_data
from loguru import logger
from web3 import Web3
from modules.abi_and_contract import BASESWAP_CONTRACTS, BASESWAP_ROUTER_ABI, BASE_TOKENS


def base_swap(account, w3, parametrs, procent, from_coin, to_coin, dapp):
    chain_w3 = w3
    address = chain_w3.to_checksum_address(account.address)
    baseswap_router = chain_w3.to_checksum_address(BASESWAP_CONTRACTS['router'])

    try:
        value_int, value, contract_stable, from_coin, to_coin = create_value(chain_w3, procent, from_coin, to_coin,
                                                                             account)
        to_token_address = Web3.to_checksum_address(BASE_TOKENS[to_coin])
        from_token_address = Web3.to_checksum_address(BASE_TOKENS[from_coin])

        contract = chain_w3.eth.contract(address=baseswap_router, abi=BASESWAP_ROUTER_ABI)

        amount_out_min = contract.functions.getAmountsOut(value_int, [from_token_address, to_token_address]).call()

        print(amount_out_min)

        if value_int == 0:  # если по итогу ничего не получили
            logger.error(f'[{address}] Не смогли получить баланс')
            return

        # Инициализация контракта
        if from_coin == 'ETH':

            deadline = int(chain_w3.eth.get_block('latest').timestamp) + 1200
            tx_data = get_tx_data(address, chain_w3, value_int)

            # Создание транзы
            swap_txn = contract.functions.swapExactETHForTokens(
                amount_out_min[1],
                [from_token_address,
                 to_token_address],
                address,
                deadline
            ).build_transaction(tx_data)

        else:
            tx_data = get_tx_data(address, chain_w3)
            allowance(chain_w3, value_int, baseswap_router, contract_stable, account)
            deadline = int(chain_w3.eth.get_block('latest').timestamp) + 1200

            swap_txn = contract.functions.swapExactTokensForETH(
                value_int,
                amount_out_min[1],
                [from_token_address,
                 to_token_address],
                address,
                deadline
            ).build_transaction(tx_data)

        estimated_gas = int(chain_w3.eth.estimate_gas(swap_txn) * 1.2)
        swap_txn['gas'] = estimated_gas

        success_tx, swap_txn_hash = sing_and_chek_tx(chain_w3, swap_txn, account)
        if success_tx:
            logger.info(f"https://basescan.org/tx/{swap_txn_hash.hex()}")
            logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                           f'[{address}][{dapp}] Successfully swap {value} {from_coin} to {to_coin}')
        else:
            logger.error(f'[{address}][{dapp}] swap error to [{to_coin}]')
    except Exception as err:
        logger.error(f'[{address}][{dapp}] swap error to [{to_coin}]: {type(err).__name__} {str(err)}')
