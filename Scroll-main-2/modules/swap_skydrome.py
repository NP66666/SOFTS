from modules.helper import sing_and_chek_tx_legasy, allowance, create_value, get_tx_data
from loguru import logger
from web3 import Web3
from modules.abi_and_contract import SKYDROME_ROUTER_ABI, SKYDROME_CONTRACTS, SCROLL_TOKENS
from web3.middleware import geth_poa_middleware


def get_min_amount_out(amount, from_token_address, to_token_address, w3):
    contract = w3.eth.contract(address=SKYDROME_CONTRACTS["router"], abi=SKYDROME_ROUTER_ABI)

    min_amount_out, swap_type = contract.functions.getAmountOut(
        amount,
        Web3.to_checksum_address(from_token_address),
        Web3.to_checksum_address(to_token_address)
    ).call()
    return int(min_amount_out * (1 - 0.03)), swap_type


def skydrome_swap(account, w3, parametrs, procent, from_coin, to_coin, dapp):
    chain_w3 = w3
    address = chain_w3.to_checksum_address(account.address)
    contract = w3.eth.contract(address=SKYDROME_CONTRACTS["router"], abi=SKYDROME_ROUTER_ABI)

    if geth_poa_middleware not in chain_w3.middleware_onion:
        chain_w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    try:
        value_int, value, contract_stable, from_coin, to_coin = create_value(chain_w3, procent, from_coin, to_coin,
                                                                             account)
        to_token_address = Web3.to_checksum_address(SCROLL_TOKENS[to_coin])
        from_token_address = Web3.to_checksum_address(SCROLL_TOKENS[from_coin])

        amount_out_min, swap_type = get_min_amount_out(value_int, from_token_address, to_token_address, chain_w3)

        if value_int == 0:  # если по итогу ничего не получили
            logger.error(f'[{address}] Не смогли получить баланс')
            return

        # Инициализация контракта
        if from_coin == 'ETH':
            deadline = int(chain_w3.eth.get_block('latest').timestamp) + 1200
            tx_data = get_tx_data(address, chain_w3, value_int)

            swap_txn = contract.functions.swapExactETHForTokens(
                amount_out_min,
                [
                    [
                        Web3.to_checksum_address(SCROLL_TOKENS[from_coin]),
                        Web3.to_checksum_address(SCROLL_TOKENS[to_coin]),
                        swap_type
                    ]
                ],
                address,
                deadline
            ).build_transaction(tx_data)
            estimated_gas = int(chain_w3.eth.estimate_gas(swap_txn) * 1.2)
            swap_txn['gas'] = estimated_gas

        else:
            allowance(chain_w3, value_int, SKYDROME_CONTRACTS["router"], contract_stable, account)
            deadline = int(chain_w3.eth.get_block('latest').timestamp) + 1200
            tx_data = get_tx_data(address, chain_w3)

            swap_txn = contract.functions.swapExactTokensForETH(
                value_int,
                amount_out_min,
                [
                    [
                        Web3.to_checksum_address(SCROLL_TOKENS[from_coin]),
                        Web3.to_checksum_address(SCROLL_TOKENS[to_coin]),
                        swap_type
                    ]
                ],
                address,
                deadline
            ).build_transaction(tx_data)

            estimated_gas = int(chain_w3.eth.estimate_gas(swap_txn) * 1.2)
            swap_txn['gas'] = estimated_gas

        success_tx, swap_txn_hash = sing_and_chek_tx_legasy(chain_w3, swap_txn, account)
        if success_tx:
            logger.info(f"https://scrollscan.com/tx/{swap_txn_hash.hex()}")
            logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                           f'[{address}][{dapp}] Successfully swap {value} {from_coin} to {to_coin}')
        else:
            logger.error(f'[{address}][{dapp}] swap error to [{to_coin}]')
    except Exception as err:
        logger.error(f'[{address}][{dapp}] swap error to [{to_coin}]: {type(err).__name__} {str(err)}')
