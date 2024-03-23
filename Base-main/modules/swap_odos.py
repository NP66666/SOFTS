import requests
from loguru import logger
from web3 import Web3
from modules.abi_and_contract import ODOS_CONTRACT, BASE_TOKENS
from modules.helper import get_tx_data, allowance, create_value, sing_and_chek_tx


def call_odos_api(from_token, to_token, amount, slippage, w3, address):
    url = "https://api.odos.xyz/sor/quote/v2"

    data = {
        "chainId": w3.eth.chain_id,
        "inputTokens": [
            {
                "tokenAddress": Web3.to_checksum_address(from_token),
                "amount": str(amount)
            }
        ],
        "outputTokens": [
            {
                "tokenAddress": Web3.to_checksum_address(to_token),
                "proportion": 1
            }
        ],
        "slippageLimitPercent": slippage,
        "userAddr": address,
        "referralCode": 0,
        "compact": True
    }

    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error("Error calling ODOS API")
        return None


def assemble_odos_transaction(path_id, address):
    url = "https://api.odos.xyz/sor/assemble"

    data = {
        "userAddr": address,
        "pathId": path_id,
        "simulate": False,
    }

    response = requests.post(url, headers={"Content-Type": "application/json"}, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"[{address}] Bad Odos request")
        return None


def odos_swap(account, w3, parametrs, procent, from_coin, to_coin, dapp):
    ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'
    chain_w3 = w3
    router_address = chain_w3.to_checksum_address(ODOS_CONTRACT['router'])
    address = chain_w3.to_checksum_address(account.address)

    try:
        value_int, value, contract_stable, from_coin, to_coin = create_value(chain_w3, procent, from_coin, to_coin,
                                                                             account)

        from_token_address = ZERO_ADDRESS if from_coin == "ETH" else BASE_TOKENS[from_coin]
        to_token_address = ZERO_ADDRESS if to_coin == "ETH" else BASE_TOKENS[to_coin]

        if from_coin != 'ETH':
            allowance(chain_w3, value_int, router_address, contract_stable, account)

        quote_data = call_odos_api(from_token_address, to_token_address, value_int, 3, chain_w3, address)
        if quote_data is None:
            logger.error("Failed to get quote data")
            return

        transaction_data = assemble_odos_transaction(quote_data["pathId"], address)
        transaction = transaction_data["transaction"]

        if transaction_data is None:
            logger.error("Failed to assemble transaction data")
            return

        tx_data = get_tx_data(address, chain_w3)

        tx_data.update(
            {
                "to": chain_w3.to_checksum_address(transaction["to"]),
                "data": transaction["data"],
                "value": int(transaction["value"]),
            }
        )

        estimated_gas = int(chain_w3.eth.estimate_gas(tx_data) * 1.2)
        tx_data['gas'] = estimated_gas

        success_tx, swap_txn_hash = sing_and_chek_tx(chain_w3, tx_data, account)
        if success_tx:
            logger.info(f"https://basescan.org/tx/{swap_txn_hash.hex()}")
            logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                           f'[{address}][{dapp}] Successfully swap {value} {from_coin} to {to_coin}')
        else:
            logger.error(f'[{address}][{dapp}] swap error to [{to_coin}]')
    except Exception as err:
        logger.error(f'[{address}][{dapp}] swap error to [{to_coin}]: {type(err).__name__} {str(err)}')
