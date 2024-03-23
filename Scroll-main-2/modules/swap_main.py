import random
from random import shuffle
from modules.abi_and_contract import stable_abi, SCROLL_TOKENS
from config import RPC_SCROLL, \
    MASSIV_DAPP, PROCENT_SWAP_MIN, PROCENT_SWAP_MAX, RANDOM_SWAP, SHUFFLE_WALLET, MASSIV_DAPP_POOL
from modules.helper import accounts, cheker_gwei, sleeping, PROXY_ACC, USE_PROXY
from loguru import logger
from modules.swap_syncswap import sync_swap
from modules.swap_skydrome import skydrome_swap
from modules.swap_ambient import ambient_swap
from modules.swap_izumi import izumi_swap
from web3 import Web3
from web3.middleware import geth_poa_middleware
from modules.layerbank import colateral_layerbank, pool_layerbank
from modules.bridge_off_most import wrap
from modules.deploy_contract import deploy_contract
from modules.mint import mint


def swap_main(nomer_puti, parametrs):
    max_acconts = len(accounts)
    parametrs['max_acconts'] = max_acconts

    count_max = parametrs['count_max']
    count_min = parametrs['count_min']

    chain_w3 = Web3(Web3.HTTPProvider(RPC_SCROLL))

    if geth_poa_middleware not in chain_w3.middleware_onion:
        chain_w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    for current_tranz in range(0, count_max):
        logger.info(f'Транзакция: {current_tranz + 1}/{count_max}')
        current_account = 0

        if SHUFFLE_WALLET:
            shuffle(accounts)

        for account in accounts:
            if USE_PROXY:
                proxy_list = PROXY_ACC[account.address].split(':')
                proxy = f'http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}'
                chain_w3 = Web3(
                    Web3.HTTPProvider(RPC_SCROLL, request_kwargs={"proxies": {'https': proxy, 'http': proxy}}))
            cheker_gwei()
            current_account += 1
            parametrs['current_account'] = current_account

            if (current_tranz + 1) > random.randint(count_min, count_max):  # проверка на кол-во
                continue

            procent = random.randint(parametrs['procent_min'], parametrs['procent_max'])

            if RANDOM_SWAP:
                eth_balance = 3000*chain_w3.eth.get_balance(account.address)/10**18 #in USDT
                contract_USDC = chain_w3.eth.contract(address=SCROLL_TOKENS['USDC'], abi=stable_abi)
                balance_USDC = contract_USDC.functions.balanceOf(account.address).call()/10**6

                if balance_USDC>eth_balance:
                    nomer_puti = 2
                else:
                    nomer_puti = 1
                procent = random.randint(PROCENT_SWAP_MIN, PROCENT_SWAP_MAX)

            if nomer_puti == 1:  # в USDC
                from_coin = 'ETH'
                to_coin = 'USDC'
            else:  # в ETH
                from_coin = 'USDC'
                to_coin = 'ETH'

            shuffle(MASSIV_DAPP)

            if MASSIV_DAPP[0] == 'Syncswap' and 'wrap_check' not in parametrs:
                sync_swap(account, chain_w3, parametrs, procent, from_coin, to_coin, MASSIV_DAPP[0])
            elif MASSIV_DAPP[0] == 'Skydrome' and 'wrap_check' not in parametrs:
                skydrome_swap(account, chain_w3, parametrs, procent, from_coin, to_coin, MASSIV_DAPP[0])
            elif MASSIV_DAPP[0] == 'Ambient' and 'wrap_check' not in parametrs:
                ambient_swap(account, chain_w3, parametrs, procent, from_coin, to_coin, MASSIV_DAPP[0])
            elif MASSIV_DAPP[0] == 'Izumi' and 'wrap_check' not in parametrs:
                izumi_swap(account, chain_w3, parametrs, procent, from_coin, to_coin, MASSIV_DAPP[0])
            elif 'wrap_check' in parametrs:
                if parametrs['wrap_check'] == 3:
                    wrap(account, parametrs, chain_w3)
            sleeping()


def pool_main(parametrs):
    max_acconts = len(accounts)
    parametrs['max_acconts'] = max_acconts

    if parametrs['deploy'] == 0:
        procent_min = parametrs['procent_min']
        procent_max = parametrs['procent_max']

    chain_w3 = Web3(Web3.HTTPProvider(RPC_SCROLL))

    if geth_poa_middleware not in chain_w3.middleware_onion:
        chain_w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if SHUFFLE_WALLET:
        shuffle(accounts)

    for current_account, account in enumerate(accounts):
        if USE_PROXY:
            proxy_list = PROXY_ACC[account.address].split(':')
            proxy = f'http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}'
            chain_w3 = Web3(Web3.HTTPProvider(RPC_SCROLL, request_kwargs={"proxies": {'https': proxy, 'http': proxy}}))
        cheker_gwei()
        parametrs['current_account'] = current_account + 1
        dapp = random.choice(MASSIV_DAPP_POOL)
        if dapp == 'layerbank' and parametrs['deploy'] == 0:
            pool_layerbank(dapp, chain_w3, account, parametrs, random.randint(procent_min, procent_max))
        elif parametrs['deploy'] == 1:
            deploy_contract(chain_w3, account, parametrs)
        sleeping()


def colateral_main(parametrs):
    max_acconts = len(accounts)
    parametrs['max_acconts'] = max_acconts
    print(f'Загружено {max_acconts} кошельков')

    count_max = parametrs['count_max']
    count_min = parametrs['count_min']

    for current_tranz in range(0, count_max):
        logger.info(f'Транзакция: {current_tranz + 1}/{count_max}')

        chain_w3 = Web3(Web3.HTTPProvider(RPC_SCROLL))

        if SHUFFLE_WALLET:
            shuffle(accounts)
        for current_account, account in enumerate(accounts):
            if USE_PROXY:
                proxy_list = PROXY_ACC[account.address].split(':')
                proxy = f'http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}'
                chain_w3 = Web3(
                    Web3.HTTPProvider(RPC_SCROLL, request_kwargs={"proxies": {'https': proxy, 'http': proxy}}))
            cheker_gwei()
            if (current_tranz + 1) > random.randint(count_min, count_max):  # проверка на кол-во
                continue
            current_account += 1
            parametrs['current_account'] = current_account

            dapp = random.choice(MASSIV_DAPP_POOL)
            if dapp == 'layerbank':
                colateral_layerbank(dapp, chain_w3, account, parametrs)
            sleeping()


def mint_main(parametrs):
    max_acconts = len(accounts)
    parametrs['max_acconts'] = max_acconts
    print(f'Загружено {max_acconts} кошельков')

    chain_w3 = Web3(Web3.HTTPProvider(RPC_SCROLL))

    if SHUFFLE_WALLET:
        shuffle(accounts)
    for current_account, account in enumerate(accounts):
        if USE_PROXY:
            proxy_list = PROXY_ACC[account.address].split(':')
            proxy = f'http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}'
            chain_w3 = Web3(
                Web3.HTTPProvider(RPC_SCROLL, request_kwargs={"proxies": {'https': proxy, 'http': proxy}}))
        cheker_gwei()
        parametrs['current_account'] = current_account+1
        try:
            mint(chain_w3, account, parametrs)
        except Exception as err:
            logger.error(f'[{account.address}] error: {type(err).__name__} {err}')

        sleeping()
