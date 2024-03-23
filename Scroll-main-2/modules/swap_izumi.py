from modules.helper import sing_and_chek_tx_legasy, allowance, create_value
from loguru import logger
from web3 import Web3
from modules.abi_and_contract import (IZUMI_QUOTER_CONTRACT, IZUMI_ROUTER_CONTRACT, IZUMI_ROUTER_ABI, IZUMI_QUOTER_ABI,
                                      SCROLL_TOKENS)
from web3.middleware import geth_poa_middleware
from hexbytes import HexBytes
from time import time


def get_amount_out_min(amount, path, chain_w3):
    contract = chain_w3.eth.contract(address=IZUMI_QUOTER_CONTRACT, abi=IZUMI_QUOTER_ABI)
    amounts_out, _ = contract.functions.swapAmount(amount, path).call()
    return int(amounts_out * (1 - 0.03))


def izumi_swap(account, w3, parametrs, procent, from_coin, to_coin, dapp):

    chain_w3 = w3
    address = chain_w3.to_checksum_address(account.address)

    if geth_poa_middleware not in chain_w3.middleware_onion:
        chain_w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    try:
        value_int, value, contract_stable, from_coin, to_coin = create_value(chain_w3, procent, from_coin, to_coin,
                                                                             account)

        to_token_address = Web3.to_checksum_address(SCROLL_TOKENS[to_coin])
        from_token_address = Web3.to_checksum_address(SCROLL_TOKENS[from_coin])

        from_token_bytes = HexBytes(from_token_address).rjust(20, b'\0')
        to_token_bytes = HexBytes(to_token_address).rjust(20, b'\0')

        num_to_bytes = 3000
        fee_bytes = num_to_bytes.to_bytes(3, 'big')

        path = from_token_bytes + fee_bytes + to_token_bytes

        amount_out_min = get_amount_out_min(value_int, path, chain_w3)


        if value_int == 0:  # если по итогу ничего не получили
            logger.error(f'[{address}] Не смогли получить баланс')
            return

        # Инициализация контракта
        if from_coin != 'ETH':
            allowance(chain_w3, value_int, IZUMI_ROUTER_CONTRACT, contract_stable, account)

        native_eth_address = "0x0000000000000000000000000000000000000000"

        router_contract = chain_w3.eth.contract(address=IZUMI_ROUTER_CONTRACT, abi=IZUMI_ROUTER_ABI)

        deadline = int(time()) + 1800

        # Создание транзы
        tx_data = router_contract.encodeABI(
            fn_name='swapAmount',
            args=[(
                path,
                address if to_coin != 'ETH' else native_eth_address,
                value_int,
                amount_out_min,
                deadline
            )]
        )

        full_data = [tx_data]

        if from_coin == 'ETH' or to_coin == 'ETH':
            tx_additional_data = router_contract.encodeABI(
                fn_name='unwrapWETH9' if from_coin != 'ETH' else 'refundETH',
                args=[
                    amount_out_min,
                    address
                ] if from_coin != 'ETH' else None
            )
            full_data.append(tx_additional_data)

        swap_txn = router_contract.functions.multicall(
            full_data
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
