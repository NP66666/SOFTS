import random
import time
from time import sleep
from config import USE_PROXY, GWEI_CONTROL, POVTOR_TX, PAUSA_MAX, PAUSA_MIN, MIN_ETH_ON_WALLET
from modules.abi_and_contract import stable_abi, SCROLL_TOKENS, SYNCSWAP_CONTRACTS, SYNCSWAP_CLASSIC_POOL_ABI, \
    SYNCSWAP_CLASSIC_POOL_DATA_ABI
from loguru import logger
from tqdm import tqdm
from web3 import Account
from web3 import Web3
from web3.middleware import geth_poa_middleware

w3_eth = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))


def sleeping(ot=PAUSA_MIN, do=PAUSA_MAX):
    x = random.randint(ot, do)
    for _ in tqdm(range(x), desc='sleep ', bar_format='{desc}: {n_fmt}/{total_fmt}'):
        time.sleep(1)


def get_amount_out_min(amount, from_token_address, to_token_address, w3, address):
    contract = w3.eth.contract(address=SYNCSWAP_CONTRACTS["classic_pool"], abi=SYNCSWAP_CLASSIC_POOL_ABI)
    pool_address = contract.functions.getPool(
            w3.to_checksum_address(from_token_address),
            w3.to_checksum_address(to_token_address)
        ).call()
    contract = w3.eth.contract(address=pool_address, abi=SYNCSWAP_CLASSIC_POOL_DATA_ABI)
    amounts_out = contract.functions.getAmountOut(from_token_address, amount, address).call()
    return int(amounts_out * (1 - 0.03)), pool_address


def cheker_gwei():
    max_gwei = GWEI_CONTROL * 10 ** 9
    try:
        if w3_eth.eth.gas_price > max_gwei:
            logger.info('Газ большой, пойду спать')
            while w3_eth.eth.gas_price > max_gwei:
                sleep(60)
            logger.info('Газ в норме. Продолжаю работу')
    except:
        sleep(60)
        cheker_gwei()


with open('keys.txt', 'r') as keys_file:
    accounts = [Account.from_key(line.replace("\n", "")) for line in keys_file.readlines()]

with open('proxy.txt', 'r') as proxy_file:
    proxys = [line.strip() for line in proxy_file]

print(f'Загружено {len(accounts)} кошельков')

PROXY_ACC = {}

if len(proxys) != len(accounts) and USE_PROXY:
    print('Количество прокси и приватников разное!!! Отменяем использование прокси.')
    USE_PROXY = False
else:
    wal_data = list(zip(proxys, accounts))
    for proxy, acc in wal_data:
        PROXY_ACC[acc.address] = proxy


def sing_and_chek_tx(chain_w3, swap_txn, account):
    retry = 0
    while retry <= POVTOR_TX:
        try:
            retry += 1
            swap_txn['nonce'] = chain_w3.eth.get_transaction_count(account.address)
            swap_txn['maxFeePerGas'] = chain_w3.eth.gas_price
            swap_txn['maxPriorityFeePerGas'] = chain_w3.eth.gas_price

            signed_swap_txn = chain_w3.eth.account.sign_transaction(swap_txn, account.key)
            swap_txn_hash = chain_w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)
            sleep(2)
            status = chain_w3.eth.wait_for_transaction_receipt(swap_txn_hash, timeout=360).status
            if status == 1:
                return True, swap_txn_hash
            else:
                logger.error(f'[{account.address}] transaction failed!')
                sleep(15)
        except Exception as err:
            if 'insufficient funds' in str(err):
                logger.error(f"[{account.address}] Error send: НЕХВАТКА БАЛАНСА")
            else:
                logger.error(f'[{account.address}] error: {type(err).__name__} {err}')
            if retry <= POVTOR_TX:
                logger.info(f'[{retry}/{POVTOR_TX}] trying again...')
                sleep(30)
    return False, ''


def sing_and_chek_tx_legasy(chain_w3, swap_txn, account):
    retry = 0
    while retry <= POVTOR_TX:
        try:
            retry += 1
            swap_txn['nonce'] = chain_w3.eth.get_transaction_count(account.address)
            swap_txn['gasPrice'] = chain_w3.eth.gas_price
            signed_swap_txn = chain_w3.eth.account.sign_transaction(swap_txn, account.key)
            swap_txn_hash = chain_w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)
            sleep(2)
            status = chain_w3.eth.wait_for_transaction_receipt(swap_txn_hash, timeout=360).status
            if status == 1:
                return True, swap_txn_hash
            else:
                logger.error(f'[{account.address}] transaction failed!')
                sleep(15)
        except Exception as err:
            if 'insufficient funds' in str(err):
                logger.error(f"[{account.address}] Error send: НЕХВАТКА БАЛАНСА")
            else:
                logger.error(f'[{account.address}] error: {type(err).__name__} {err}')
            if retry <= POVTOR_TX:
                logger.info(f'[{retry}/{POVTOR_TX}] trying again...')
                sleep(30)
    return False, ''


def allowance(chain_w3, value_int, router_address, contract_stable, account):

    if geth_poa_middleware not in chain_w3.middleware_onion:
        chain_w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    allowance_full = contract_stable.functions.allowance(account.address, router_address).call()
    amount = value_int

    if allowance_full < amount:
        amount_new = amount * 100
        approve_txn = contract_stable.functions.approve(router_address, amount_new).build_transaction({
            'from': account.address,
            'gasPrice': chain_w3.eth.gas_price,
            'nonce': chain_w3.eth.get_transaction_count(account.address),
        })
        estimated_gas = int(chain_w3.eth.estimate_gas(approve_txn) * 1.2)
        approve_txn['gas'] = estimated_gas
        signed_swap_txn = chain_w3.eth.account.sign_transaction(approve_txn, account.key)

        swap_txn_hash = chain_w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)
        sleep(5)

        status = chain_w3.eth.wait_for_transaction_receipt(swap_txn_hash, timeout=360).status
        if status == 1:
            logger.info(f"https://scrollscan.com/tx/{swap_txn_hash.hex()}")
            logger.success(f' Successfully APPROVED')
        time.sleep(20)


def get_tx_data(address, w3, value: int = 0):
    tx = {
        "chainId": w3.eth.chain_id,
        "from": address,
        "value": value,
        "nonce": w3.eth.get_transaction_count(address),
    }

    if w3.eth.get_block('latest').get('baseFeePerGas'):
        tx['maxFeePerGas'] = w3.eth.get_block('latest')['baseFeePerGas'] * 2
        tx['maxPriorityFeePerGas'] = w3.toWei('1', 'gwei')
    else:
        tx['gasPrice'] = int(w3.eth.gas_price*1.2)

    return tx


def create_value(chain_w3, procent, from_coin, to_coin, account, popitka=0):
    if popitka == 2:
        return 0, 0, False, from_coin, to_coin

    if from_coin == 'ETH':
        balance = (float(
            chain_w3.from_wei(chain_w3.eth.get_balance(account.address), "ether")) - MIN_ETH_ON_WALLET) * procent / 100

        if balance <= 0:
            return create_value(chain_w3, procent, 'USDC', 'ETH', account, popitka+1)

        balance_int = chain_w3.to_wei(balance, 'ether')
        balance = round(balance, 6)
        balance = '{:6f}'.format(balance).rstrip('0')
        return balance_int, balance, False, from_coin, to_coin
    else:
        balance_contract = chain_w3.eth.contract(address=SCROLL_TOKENS[from_coin], abi=stable_abi)
        balance_int = (balance_contract.functions.balanceOf(account.address).call() * procent) // 100

        if balance_int <= 0:
            return create_value(chain_w3, procent, 'ETH', 'USDC', account, popitka+1)

        balance = round(balance_int / 10**6, 4)
        balance = '{:6f}'.format(balance).rstrip('0')

        return balance_int, balance, balance_contract, from_coin, to_coin


def approve(w3, amount, token_address: str, contract_address: str, account):
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    token_address = Web3.to_checksum_address(token_address)
    contract_address = Web3.to_checksum_address(contract_address)

    contract = w3.eth.contract(address=token_address, abi=stable_abi)

    amount_approved = contract.functions.allowance(token_address, contract_address).call()

    if amount > amount_approved:
        logger.info(f"[{account.address}] Making approve")

        approve_amount = 2 ** 128 if amount > amount_approved else 0

        tx_data = get_tx_data(account.address, w3)

        transaction = contract.functions.approve(
            contract_address,
            approve_amount
        ).build_transaction(tx_data)

        signed_swap_txn = w3.eth.account.sign_transaction(transaction, account.key)
        swap_txn_hash = w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)
        sleep(5)
        status = w3.eth.wait_for_transaction_receipt(swap_txn_hash, timeout=360).status
        if status == 1:
            logger.info(f"https://scrollscan.com/tx/{swap_txn_hash.hex()}")
            logger.success(f' Successfully APPROVED')
        time.sleep(10)
    else:
        pass
