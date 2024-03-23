import random
from random import shuffle
from config import RPC_LINEA, \
    MASSIV_DAPP, PROCENT_SWAP_MIN, PROCENT_SWAP_MAX, RANDOM_SWAP, SHUFFLE_WALLET, MASSIV_DAPP_POOL
from helper import accounts, cheker_gwei, sleeping, PROXY_ACC, USE_PROXY
from loguru import logger
from swap_syncswap import sync_swap
from swap_echodex import echodex_swap
from swap_horizondex import horizondex_swap
from web3 import Web3
from web3.middleware import geth_poa_middleware
from layerbank import colateral_layerbank, pool_layerbank


def swap_main(nomer_puti, parametrs):

    max_acconts = len(accounts)
    parametrs['max_acconts'] = max_acconts

    count_max = parametrs['count_max']
    count_min = parametrs['count_min']

    chain_w3 = Web3(Web3.HTTPProvider(RPC_LINEA))
    if geth_poa_middleware not in chain_w3.middleware_onion:
        chain_w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    for current_tranz in range(0, count_max):
        logger.info(f'Транзакция: {current_tranz+1}/{count_max}')
        current_account = 0

        if SHUFFLE_WALLET: shuffle(accounts)

        for account in accounts:
            if USE_PROXY:
                proxy_list = PROXY_ACC[account.address].split(':')
                proxy = f'http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}'
                chain_w3 = Web3(Web3.HTTPProvider(RPC_LINEA, request_kwargs={"proxies": {'https': proxy, 'http': proxy}}))
            cheker_gwei()
            current_account += 1
            parametrs['current_account'] = current_account

            if (current_tranz+1) > random.randint(count_min, count_max):#проверка на кол-во
                continue

            procent = random.randint(parametrs['procent_min'], parametrs['procent_max'])

            if RANDOM_SWAP:
                nomer_puti = random.randint(1, 2)
                procent = random.randint(PROCENT_SWAP_MIN, PROCENT_SWAP_MAX)

            if nomer_puti == 1:  # в BUSD
                from_coin = 'ETH'
                to_coin = 'BUSD'
            else:  # в ETH
                from_coin = 'BUSD'
                to_coin = 'ETH'

            shuffle(MASSIV_DAPP)

            if MASSIV_DAPP[0] == 'SyncSwap':
                sync_swap(account, chain_w3, parametrs, procent, from_coin, to_coin, MASSIV_DAPP[0])
            elif MASSIV_DAPP[0] == 'ECHODEX':
                echodex_swap(account, chain_w3, parametrs, procent, from_coin, to_coin, MASSIV_DAPP[0])
            elif MASSIV_DAPP[0] == 'horizondex':
                horizondex_swap(account, chain_w3, parametrs, procent, from_coin, to_coin, MASSIV_DAPP[0])
            sleeping()


def pool_main(parametrs):

    max_acconts = len(accounts)
    parametrs['max_acconts'] = max_acconts

    procent_min = parametrs['procent_min']
    procent_max = parametrs['procent_max']

    chain_w3 = Web3(Web3.HTTPProvider(RPC_LINEA))

    if SHUFFLE_WALLET:
        shuffle(accounts)

    for current_account, account in enumerate(accounts):
        if USE_PROXY:
            proxy_list = PROXY_ACC[account.address].split(':')
            proxy = f'http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}'
            chain_w3 = Web3(Web3.HTTPProvider(RPC_LINEA, request_kwargs={"proxies": {'https': proxy, 'http': proxy}}))
        cheker_gwei()
        parametrs['current_account'] = current_account+1
        dapp = random.choice(MASSIV_DAPP_POOL)
        if dapp == 'layerbank':
            pool_layerbank(dapp, chain_w3, account, parametrs, random.randint(procent_min, procent_max))
        sleeping()


def colateral_main(parametrs):

    max_acconts = len(accounts)
    parametrs['max_acconts'] = max_acconts
    print(f'Загружено {max_acconts} кошельков')

    count_max = parametrs['count_max']
    count_min = parametrs['count_min']

    for current_tranz in range(0, count_max):
        logger.info(f'Транзакция: {current_tranz + 1}/{count_max}')

        chain_w3 = Web3(Web3.HTTPProvider(RPC_LINEA))

        if SHUFFLE_WALLET:
            shuffle(accounts)
        for current_account, account in enumerate(accounts):
            if USE_PROXY:
                proxy_list = PROXY_ACC[account.address].split(':')
                proxy = f'http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}'
                chain_w3 = Web3(Web3.HTTPProvider(RPC_LINEA, request_kwargs={"proxies": {'https': proxy, 'http': proxy}}))
            cheker_gwei()
            if (current_tranz + 1) > random.randint(count_min, count_max):  # проверка на кол-во
                continue
            parametrs['current_account'] = current_account+1

            dapp = random.choice(MASSIV_DAPP_POOL)
            if dapp == 'layerbank':
                colateral_layerbank(dapp, chain_w3, account, parametrs)
            else:
                colateral_layerbank(dapp, chain_w3, account, parametrs)
            sleeping()
