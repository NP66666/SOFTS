from eth_abi import abi
from modules.helper import sing_and_chek_tx_legasy, allowance, create_value, get_amount_out_min
from loguru import logger
from web3 import Web3
from modules.abi_and_contract import SYNCSWAP_CONTRACTS, SCROLL_TOKENS, SYNCSWAP_ROUTER_ABI
from web3.middleware import geth_poa_middleware


def sync_swap(account, w3, parametrs, procent, from_coin, to_coin, dapp):

    chain_w3 = w3
    address = chain_w3.to_checksum_address(account.address)
    sync_swap_router_address = chain_w3.to_checksum_address(SYNCSWAP_CONTRACTS['router'])

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
            allowance(chain_w3, value_int, sync_swap_router_address, contract_stable, account)

        swap_data = abi.encode(["address", "address", "uint8"], [from_token_address, address, 1])
        native_eth_address = "0x0000000000000000000000000000000000000000"

        steps = [{
            "pool": pool_address,
            "data": swap_data,
            "callback": native_eth_address,
            "callbackData": '0x'
        }]

        paths = [{
            "steps": steps,
            "tokenIn": from_token_address if from_coin != 'ETH' else native_eth_address,
            "amountIn": value_int,
        }]

        contract = chain_w3.eth.contract(address=sync_swap_router_address, abi=SYNCSWAP_ROUTER_ABI)
        deadline = int(chain_w3.eth.get_block('latest').timestamp) + 1200

        # Создание транзы
        swap_txn = contract.functions.swap(
            paths,
            amount_out_min,
            deadline
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
