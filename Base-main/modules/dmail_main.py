import random
import time
from random import shuffle
from config import RPC_BASE, SHUFFLE_WALLET
from modules.helper import accounts, cheker_gwei, sleeping, PROXY_ACC, USE_PROXY
from loguru import logger
from web3 import Web3
from modules.abi_and_contract import DMAIL_ABI, DMAIL_CONTRACT
from hashlib import sha256


def dmail_main(parametrs):
    max_acconts = len(accounts)
    parametrs['max_acconts'] = max_acconts

    count_max = parametrs['count_max']
    count_min = parametrs['count_min']

    chain_w3 = Web3(Web3.HTTPProvider(RPC_BASE))

    for current_tranz in range(0, count_max):
        logger.info(f'Письмо: {current_tranz + 1}/{count_max}')
        current_account = 0

        if SHUFFLE_WALLET:
            shuffle(accounts)

        for account in accounts:
            if USE_PROXY:
                proxy_list = PROXY_ACC[account.address].split(':')
                proxy = f'http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}'
                chain_w3 = Web3(
                    Web3.HTTPProvider(RPC_BASE, request_kwargs={"proxies": {'https': proxy, 'http': proxy}}))
            cheker_gwei()
            current_account += 1
            parametrs['current_account'] = current_account

            if (current_tranz + 1) > random.randint(count_min, count_max):  # проверка на кол-во
                continue

            send_mail(account, chain_w3, parametrs)

            sleeping()


def send_mail(account, chain_w3, parametrs):
    email_address = sha256(str(1e11 * random.random()).encode()).hexdigest()
    theme = sha256(str(1e11 * random.random()).encode()).hexdigest()

    address = account.address
    contract = chain_w3.eth.contract(address=Web3.to_checksum_address(DMAIL_CONTRACT), abi=DMAIL_ABI)
    swap_txn = {
        "chainId": chain_w3.eth.chain_id,
        "from": account.address,
        "to": Web3.to_checksum_address(DMAIL_CONTRACT),
        "gasPrice": chain_w3.eth.gas_price,
        "nonce": chain_w3.eth.get_transaction_count(account.address)
    }
    try:
        data = contract.encodeABI("send_mail", args=(email_address, theme))

        swap_txn.update({"data": data})
        gas = chain_w3.eth.estimate_gas(swap_txn)
        gas = int(gas + gas * 0.3)
        swap_txn.update({"gas": gas})

        signed_swap_txn = chain_w3.eth.account.sign_transaction(swap_txn, account.key)
        swap_txn_hash = chain_w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)
        time.sleep(2)
        status = chain_w3.eth.wait_for_transaction_receipt(swap_txn_hash, timeout=360).status
        if status == 1:
            logger.info(f"https://basescan.org/tx/{swap_txn_hash.hex()}")
            logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                           f'[{address}] Successfully sent!')
        else:
            logger.error(f'[{address}] send error')
    except Exception as err:
        if 'insufficient funds' in str(err):
            logger.error(f"[{address}] Error send: НЕХВАТКА БАЛАНСА")
        else:
            logger.error(f"[{address}] Error send: {type(err).__name__} {err}")
