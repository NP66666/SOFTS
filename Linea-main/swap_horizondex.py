from config import LINEA_TOKENS
from helper import sing_and_chek_tx, allowance, create_value, get_amount_out_min
from loguru import logger
from web3 import Web3
from abi_and_contract import horizondex_router_abi, horizondex_contract
from web3.middleware import geth_poa_middleware
from eth_abi import encode
from hexbytes import HexBytes


def horizondex_swap(account, w3, parametrs, procent, from_coin, to_coin, dapp):
    chain_w3 = w3
    if geth_poa_middleware not in w3.middleware_onion:
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    address = account.address
    try:
        value_int, value, contract_stable, from_coin, to_coin = create_value(chain_w3, procent, from_coin, to_coin, account)

        to_token_address = Web3.to_checksum_address(LINEA_TOKENS[to_coin])
        from_token_address = Web3.to_checksum_address(LINEA_TOKENS[from_coin])

        if value_int == 0:  # если по итогу ничего не получили
            logger.error(f'[{address}] Не смогли получить баланс')
            return

        swap_contract = chain_w3.eth.contract(address=Web3.to_checksum_address(horizondex_contract), abi=horizondex_router_abi)
        if from_coin != 'ETH':
            allowance(chain_w3, value_int, Web3.to_checksum_address(horizondex_contract), contract_stable, account)

        deadline = int(w3.eth.get_block('latest').timestamp) + 1200

        amount_out_min = get_amount_out_min(value_int, from_token_address, to_token_address, chain_w3)

        if from_coin == 'ETH':
            tx_data = [
                from_token_address,
                to_token_address,
                300,
                address,
                deadline,
                value_int,
                int(amount_out_min),
                0
            ]

            swap_txn = swap_contract.functions.swapExactInputSingle(tx_data)

        else:
            swap_data = encode([
                'address', 'address', 'uint24', 'address', 'uint256', 'uint256', 'uint256', 'uint160'
            ], [
                from_token_address,
                to_token_address,
                300,
                Web3.to_checksum_address('0x0000000000000000000000000000000000000000'),
                deadline,
                value_int,
                int(amount_out_min),
                0
            ]).hex()

            unwrap_data = encode(['uint256', 'address'],
                                 [int(amount_out_min), address]).hex()

            swap_txn = swap_contract.functions.multicall(
                [HexBytes('0xa8c9ed67' + swap_data), HexBytes('0xbac37ef7' + unwrap_data)]
            )

        swap_txn = swap_txn.build_transaction({
            'value': value_int if from_coin == 'ETH' else 0,
            'from': address,
            'maxFeePerGas': int(chain_w3.eth.gas_price * 1.3),
            'maxPriorityFeePerGas': chain_w3.eth.max_priority_fee,
            'gas': 0
        })

        estimated_gas = int(chain_w3.eth.estimate_gas(swap_txn) * 1.3)
        swap_txn['gas'] = estimated_gas

        success_tx, swap_txn_hash = sing_and_chek_tx(chain_w3, swap_txn, account)
        if success_tx:
            logger.info(f"https://lineascan.build/tx/{swap_txn_hash.hex()}")
            logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                           f'[{address}][{dapp}] Successfully swap {value} {from_coin} to {to_coin}')
        else:
            logger.error(f'[{address}][{dapp}] swap error to [{to_coin}]')
    except Exception as err:
        logger.error(f'[{address}][{dapp}] swap error to [{to_coin}]: {type(err).__name__} {err}')
