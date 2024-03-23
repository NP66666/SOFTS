from modules.helper import sing_and_chek_tx_legasy, allowance, create_value, get_amount_out_min
from loguru import logger
from web3 import Web3
from modules.abi_and_contract import AMBIENT_CONTRACT, SCROLL_TOKENS, AMBIENT_SWAP_ABI
from web3.middleware import geth_poa_middleware


def ambient_swap(account, w3, parametrs, procent, from_coin, to_coin, dapp):

    chain_w3 = w3
    address = chain_w3.to_checksum_address(account.address)

    if geth_poa_middleware not in chain_w3.middleware_onion:
        chain_w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    try:
        value_int, value, contract_stable, from_coin, to_coin = create_value(chain_w3, procent, from_coin, to_coin,
                                                                             account)
        to_token_address = Web3.to_checksum_address(SCROLL_TOKENS[to_coin])
        from_token_address = Web3.to_checksum_address(SCROLL_TOKENS[from_coin])

        amount_out_min, pool_address = get_amount_out_min(value_int, from_token_address, to_token_address, chain_w3, address)

        if value_int == 0:  # если по итогу ничего не получили
            logger.error(f'[{address}] Не смогли получить баланс')
            return

        # Инициализация контракта
        if from_coin != 'ETH':
            allowance(chain_w3, value_int, AMBIENT_CONTRACT, contract_stable, account)

        native_eth_address = "0x0000000000000000000000000000000000000000"

        contract = chain_w3.eth.contract(address=AMBIENT_CONTRACT, abi=AMBIENT_SWAP_ABI)

        # Создание транзы
        swap_txn = contract.functions.swap(
            native_eth_address,
            chain_w3.to_checksum_address(SCROLL_TOKENS['USDC']) if from_coin == 'ETH' else chain_w3.to_checksum_address(SCROLL_TOKENS['ETH']),
            420,
            True if from_coin == 'ETH' else False,
            True if from_coin == 'ETH' else False,
            value_int,
            0,
            21267430153580247136652501917186561137 if from_coin == 'ETH' else 65537,
            amount_out_min,
            0
        ).build_transaction({
            'from': address,
            'value': value_int if from_coin == 'ETH' else 0,
            'gasPrice': int(w3.eth.gas_price*1.2),
        })

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
