from json import dumps
from requests import request
from hashlib import sha256
from base64 import b64encode
from time import time_ns

from web3.middleware import geth_poa_middleware
from random import uniform
from typing import Union, Optional
from time import sleep
from web3 import Web3
import ccxt
import requests, hmac, base64

from modules.utils import logger, sleeping
from modules.const import CHAINS_DATA, STG_address, stg_contract
import settings


class Wallet:
    def __init__(self, privatekey: str, recipient: str, recipient2=None):
        self.privatekey = privatekey
        self.recipient = Web3().to_checksum_address(recipient)
        self.recipient2 = Web3().to_checksum_address(recipient2) if not recipient2 is None else None
        self.account = Web3().eth.account.from_key(privatekey)
        self.address = self.account.address
        self.max_retries = settings.RETRY
        self.stg_contract = stg_contract

    def get_web3(self, chain_name: str):
        web3 = Web3(Web3.HTTPProvider(settings.RPCS[chain_name]))
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return web3

    def wait_for_gwei(self):
        first_check = True
        while True:
            new_gwei = round(self.get_web3(chain_name='ethereum').eth.gas_price / 10 ** 9, 2)
            if new_gwei < settings.MAX_GWEI:
                if not first_check: 
                    logger.debug(f'[•] Web3 | New GWEI is {new_gwei}')
                break
            sleep(5)
            if first_check:
                first_check = False
                logger.debug(f'[•] Web3 | Waiting for GWEI at least {settings.MAX_GWEI}. Now it is {new_gwei}')

    def get_gas(self, chain_name):
        max_priority = self.get_web3(chain_name=chain_name).eth.max_priority_fee
        last_block = self.get_web3(chain_name=chain_name).eth.get_block('latest')
        base_fee = last_block['baseFeePerGas']
        block_filled = last_block['gasUsed'] / last_block['gasLimit'] * 100
        if block_filled > 50:
            base_fee *= 1.125
        if settings.GWEI_MULTIPLIER > 1:
            base_fee *= settings.GWEI_MULTIPLIER
        max_fee = int(base_fee + max_priority)

        return {'maxPriorityFeePerGas': max_fee, 'maxFeePerGas': max_fee}

    def sent_tx(self, chain_name: str, tx, tx_label, tx_raw=False, value=0):
        try:
            web3 = self.get_web3(chain_name=chain_name)
            if not tx_raw:
                tx = tx.build_transaction({
                    'from': self.address,
                    'chainId': web3.eth.chain_id,
                    'nonce': web3.eth.get_transaction_count(self.address),
                    'value': value,
                    **self.get_gas(chain_name=chain_name),
                })
                tx['gas'] = int(int(tx['gas']) * 1.1)

            signed_tx = web3.eth.account.sign_transaction(tx, self.privatekey)
            raw_tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash = web3.to_hex(raw_tx_hash)
            tx_link = f'{CHAINS_DATA[chain_name]["explorer"]}{tx_hash}'
            logger.debug(f'[•] Web3 | {tx_label} tx sent: {tx_link}')

            status = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=360).status

            if status == 1:
                logger.info(f'[+] Web3 | {tx_label} tx confirmed\n')
                return tx_hash
            else:
                raise ValueError(f'{tx_label} tx failed: {tx_link}')
        except Exception as err:
            try: encoded_tx = f'\n{tx._encode_transaction_data()}'
            except: encoded_tx = ''
            raise ValueError(f'failed: {err}{encoded_tx}')

    def get_balance(self, chain_name: str, token_name: Optional[str] = False, token_address: Optional[str] = False, human=False):
        web3 = self.get_web3(chain_name=chain_name)
        if token_name:
            token_address = STG_address[token_name]
        if token_address:
            contract = web3.eth.contract(address=web3.to_checksum_address(token_address),
                                     abi='[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]')
        while True:
            try:
                if token_address:
                    balance = contract.functions.balanceOf(self.address).call()
                else:
                    balance = web3.eth.get_balance(self.address)

                decimals = contract.functions.decimals().call() if token_address else 18
                if not human: return balance
                return balance / 10 ** decimals
            except Exception as err:
                logger.warning(f'[•] Web3 | Get balance error: {err}')
                sleep(5)


    def wait_balance(self, chain_name: str, needed_balance: Union[int, float], only_more: bool = False, token_name: Optional[str] = False, token_address: Optional[str] = False):
        " needed_balance: human digit "
        if token_name:
            token_address = STG_address[token_name]

        elif token_address:
            contract = self.get_web3(chain_name=chain_name).eth.contract(address=Web3().to_checksum_address(token_address),
                                         abi='[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}]')
            token_name = contract.functions.name().call()

        else:
            token_name = 'ETH'

        if only_more: logger.debug(f'[•] Web3 | Waiting for balance more than {round(needed_balance, 6)} {token_name} in {chain_name.upper()}')
        else: logger.debug(f'[•] Web3 | Waiting for {round(needed_balance, 6)} {token_name} balance in {chain_name.upper()}')

        while True:
            try:
                new_balance = self.get_balance(chain_name=chain_name, human=True, token_address=token_address)

                if only_more: status = new_balance > needed_balance
                else: status = new_balance >= needed_balance
                if status:
                    logger.debug(f'[•] Web3 | New balance: {round(new_balance, 6)} {token_name}')
                    return new_balance
                sleep(5)
            except Exception as err:
                logger.warning(f'[•] Web3 | Wait balance error: {err}')
                sleep(10)


    def okx_withdraw(self, chain: str, retry=0):

        def okx_data(api_key, secret_key, passphras, request_path="/api/v5/account/balance?ccy=ETH", body='', meth="GET"):

            try:
                import datetime
                def signature(
                        timestamp: str, method: str, request_path: str, secret_key: str, body: str = ""
                ) -> str:
                    if not body:
                        body = ""

                    message = timestamp + method.upper() + request_path + body
                    mac = hmac.new(
                        bytes(secret_key, encoding="utf-8"),
                        bytes(message, encoding="utf-8"),
                        digestmod="sha256",
                    )
                    d = mac.digest()
                    return base64.b64encode(d).decode("utf-8")

                dt_now = datetime.datetime.utcnow()
                ms = str(dt_now.microsecond).zfill(6)[:3]
                timestamp = f"{dt_now:%Y-%m-%dT%H:%M:%S}.{ms}Z"

                base_url = "https://www.okex.com"
                headers = {
                    "Content-Type": "application/json",
                    "OK-ACCESS-KEY": api_key,
                    "OK-ACCESS-SIGN": signature(timestamp, meth, request_path, secret_key, body),
                    "OK-ACCESS-TIMESTAMP": timestamp,
                    "OK-ACCESS-PASSPHRASE": passphras,
                    'x-simulated-trading': '0'
                }
            except Exception as ex:
                logger.error(ex)
            return base_url, request_path, headers

        self.wait_for_gwei()

        amount_from = settings.OKX_WITHDRAW_VALUES[chain][0]
        amount_to = settings.OKX_WITHDRAW_VALUES[chain][1]
        wallet = self.address
        SUB_ACC = True
        SYMBOL = 'ETH'

        match chain:
            case 'arbitrum' : CHAIN = 'Arbitrum One'
            case 'base'     : CHAIN = 'Base'
            case 'optimism' : CHAIN = 'Optimism'

        api_key = settings.OKX_KEY
        secret_key = settings.OKX_SECRET
        passphras = settings.OKX_PASSWORD

        # take FEE for withdraw
        _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/currencies?ccy={SYMBOL}",
                                 meth="GET")
        response = requests.get(f"https://www.okx.cab/api/v5/asset/currencies?ccy={SYMBOL}", timeout=10,
                                headers=headers)

        try:     
            for lst in response.json()['data']:
                if lst['chain'] == f'{SYMBOL}-{CHAIN}':
                    FEE = lst['minFee']
        except Exception as error:
            if 'data' in str(error):
                logger.error("Неверно настроил API OKX. Возможно IP не добавил или добавил лишний. Если не помогло, сделай новые API со всеми разрешениями.")
                return

        try:
            while True:
                if SUB_ACC == True:
                    _, _, headers = okx_data(api_key, secret_key, passphras,
                                             request_path=f"/api/v5/users/subaccount/list", meth="GET")
                    list_sub = requests.get("https://www.okx.cab/api/v5/users/subaccount/list", timeout=10,
                                            headers=headers)
                    list_sub = list_sub.json()

                    for sub_data in list_sub['data']:
                        while True:
                            name_sub = sub_data['subAcct']

                            _, _, headers = okx_data(api_key, secret_key, passphras,
                                                     request_path=f"/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy={SYMBOL}",
                                                     meth="GET")
                            sub_balance = requests.get(
                                f"https://www.okx.cab/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy={SYMBOL}",
                                timeout=10, headers=headers)
                            sub_balance = sub_balance.json()
                            if sub_balance.get('msg') == f'Sub-account {name_sub} doesn\'t exist':
                                logger.warning(f'[-] OKX | Error: {sub_balance["msg"]}')
                                continue
                            sub_balance = sub_balance['data'][0]['bal']

                            if float(sub_balance) > 0:
                                logger.info(f'[•] OKX | {name_sub} | {sub_balance} {SYMBOL}')

                                body = {"ccy": f"{SYMBOL}", "amt": str(sub_balance), "from": 6, "to": 6, "type": "2",
                                        "subAcct": name_sub}
                                _, _, headers = okx_data(api_key, secret_key, passphras,
                                                         request_path=f"/api/v5/asset/transfer", body=str(body),
                                                         meth="POST")
                                a = requests.post("https://www.okx.cab/api/v5/asset/transfer", data=str(body),
                                                  timeout=10, headers=headers)
                            break

                try:
                    _, _, headers = okx_data(api_key, secret_key, passphras,
                                             request_path=f"/api/v5/account/balance?ccy={SYMBOL}")
                    balance = requests.get(f'https://www.okx.cab/api/v5/account/balance?ccy={SYMBOL}', timeout=10,
                                           headers=headers)
                    balance = balance.json()
                    balance = balance["data"][0]["details"][0]["cashBal"]

                    if balance != 0:
                        body = {"ccy": f"{SYMBOL}", "amt": float(balance), "from": 18, "to": 6, "type": "0",
                                "subAcct": "", "clientId": "", "loanTrans": "", "omitPosRisk": ""}
                        _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/transfer",
                                                 body=str(body), meth="POST")
                        a = requests.post("https://www.okx.cab/api/v5/asset/transfer", data=str(body), timeout=10,
                                          headers=headers)
                except Exception as ex:
                    pass

                # CHECK MAIN BALANCE
                _, _, headers = okx_data(api_key, secret_key, passphras,
                                         request_path=f"/api/v5/asset/balances?ccy={SYMBOL}", meth="GET")
                main_balance = requests.get(f'https://www.okx.cab/api/v5/asset/balances?ccy={SYMBOL}', timeout=10,
                                            headers=headers)
                main_balance = main_balance.json()
                main_balance = float(main_balance["data"][0]['availBal'])
                logger.info(f'[•] OKX | Total balance: {main_balance} {SYMBOL}')

                if amount_from > main_balance:
                    logger.warning(f'[•] OKX | Not enough balance ({main_balance} < {amount_from}), waiting 10 secs...')
                    sleep(10)
                    continue

                if amount_to > main_balance:
                    logger.warning(
                        f'[•] OKX | You want to withdraw MAX {amount_to} but have only {round(main_balance, 7)}')
                    amount_to = round(main_balance, 7)

                AMOUNT = round(uniform(amount_from, amount_to), 7)
                break

            old_balance = self.get_balance(chain_name=chain, human=True)

            body = {"ccy": SYMBOL, "amt": AMOUNT, "fee": FEE, "dest": "4", "chain": f"{SYMBOL}-{CHAIN}",
                    "toAddr": wallet}
            _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/withdrawal",
                                     meth="POST", body=str(body))
            a = requests.post("https://www.okx.cab/api/v5/asset/withdrawal", data=str(body), timeout=10,
                              headers=headers)
            result = a.json()

            if result['code'] == '0':
                logger.success(f"[+] OKX | Success withdraw {AMOUNT} {SYMBOL} to {wallet}")
                new_balance = self.wait_balance(chain_name=chain, needed_balance=old_balance, only_more=True)
                return round(new_balance - old_balance, 6) ###
            else:
                error = result['msg']
                if retry < self.max_retries:
                    logger.error(f"[-] OKX | Withdraw unsuccess to {wallet} | error : {error}")
                    sleep(10)
                    return self.okx_withdraw(chain=chain, retry=retry + 1)
                else:
                    raise ValueError(f'OKX withdraw error: {error}')

        except Exception as error:
            logger.error(f"[-] OKX | Withdraw unsuccess to {wallet} | error : {error}")
            if retry < self.max_retries:
                sleep(10)
                if 'Insufficient balance' in str(error): return self.okx_withdraw(chain=chain, retry=retry)
                return self.okx_withdraw(chain=chain, retry=retry + 1)
            else:
                raise ValueError(f'OKX withdraw error: {error}')

    def send_to(self, chain: str, retry=0):

        try:
            web3 = self.get_web3(chain_name=chain)

            keep_values = round(uniform(settings.BALANCE_VALUES[chain][0], settings.BALANCE_VALUES[chain][1]), 7)

            balance = self.get_balance(chain_name=chain, human=True)
            amount = round(balance - keep_values, 6)
            if amount<0:
                logger.info(f'[{chain}] баланс меньше указанного')
                return
            value = int(amount * 10 ** 18)

            value = int(value - 21000 * web3.eth.gas_price * 1.1 // 10 ** 12 * 10 ** 12)  # round value
            amount = round(value / 10 ** 18, 5)

            module_str = f'sent {amount} ETH to {self.recipient2}'

            tx = {
                'from': self.address,
                'to': self.recipient2,
                'chainId': web3.eth.chain_id,
                'nonce': web3.eth.get_transaction_count(self.address),
                'value': value,
                #'gas': 1250000,
                **self.get_gas(chain_name=chain),
            }
            gasLimit = web3.eth.estimate_gas(tx)
            tx['gas'] = int(gasLimit + gasLimit * 0.5)
            self.sent_tx(chain, tx, module_str, tx_raw=True)

        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f'{error}')
                sleeping(10)
                return self.send_to(chain=chain, retry=retry + 1)

    def send_to_STG(self, chain: str, retry=0):

        try:
            web3 = self.get_web3(chain_name=chain)

            amount = self.get_balance(chain_name=chain, human=True, token_address=STG_address[chain])
            value = int(amount) * 10 ** 18
            stg_contract = self.stg_contract[chain]

            # Подготовьте данные для транзакции
            tx = stg_contract.functions.transfer(self.recipient, value)
            tx = tx.build_transaction({
                'from': self.address,
                'chainId': web3.eth.chain_id,
                #'gas': 1250000,  # арбитрум
                'nonce': web3.eth.get_transaction_count(self.address),
                **self.get_gas(chain_name=chain),
            })
            gasLimit = web3.eth.estimate_gas(tx)
            tx['gas'] = int(gasLimit + gasLimit * 0.5)

            module_str = f'sent {int(amount)} STG to {self.recipient}'
            self.sent_tx(chain, tx, module_str, tx_raw=True)

        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f'{error}')
                sleeping(10)
                return self.send_to_okx(chain=chain, retry=retry + 1)

    def bitget_withdraw(self, chain, SYMBOL, retry=0):
        all_transfer_to_main('STG')
        exchange = ccxt.bitget({
            'apiKey': settings.BITGET_KEY,
            'secret': settings.BITGET_SECRET,
            'password': settings.BITGET_PASSWORD,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        old_balance = self.get_balance(chain_name=chain, human=True, token_address=STG_address[chain])
        amount_from = settings.BITGET_WITHDRAW_VALUES[chain][0]
        amount_to = settings.BITGET_WITHDRAW_VALUES[chain][1]
        AMOUNT = round(uniform(amount_from, amount_to), 7)

        try:
            exchange.withdraw(
                code=SYMBOL,
                amount=AMOUNT,
                address=self.address,
                tag=None,
                params={
                    "chain": "ARBITRUMONE"
                }
            )
            logger.success(f"[+] Bitget | Success withdraw {AMOUNT} {SYMBOL} to {self.address}")
            self.wait_balance(chain_name=chain, needed_balance=old_balance, only_more=True, token_address=STG_address[chain])
        except Exception as error:
            print(f'[-] Bitget Не удалось вывести {AMOUNT} {SYMBOL}: {error} ', flush=True)
            sleeping(60)
            if 15>retry:
                self.bitget_withdraw(chain, SYMBOL, retry+1)


def all_transfer_to_main(coin: str):
    subacc_assets = get_subacc_assets()
    for subacc in subacc_assets['data']:
        for asset in subacc['assetsList']:
            if asset["coin"] == coin:
                if float(asset["available"]) > 0:
                    if subacc_transfer(amount=asset["available"], coin=asset["coin"], from_id=subacc["userId"]):
                        print(f'Transfered {asset["available"]} {asset["coin"]} from SubAccount №{subacc["userId"]} to Main Account')


def get_subacc_assets():
    response = send_request(
        method="GET",
        url='/api/v2/spot/account/subaccount-assets',
    )

    return response


def send_request(method: str, url: str, params: Optional[str]=None, payload: Optional[str]=None):
    headers = get_headers(method=method, url=url, params=params or payload or "")

    while True:
        try:
            r = request(method=method, url='https://api.bitget.com'+url, params=params, json=payload, headers=headers)
            break
        except ConnectionError as err:
            logger.warning(f'Send request connection error: {err}')
            sleep(5)


    if 'too many requests' in r.text.lower():
        logger.warning(f'TOO MANY REQUESTS')
        sleep(5)
        return send_request(method=method, url=url, params=params, payload=payload)

    try:
        if r.json()['code'] != '00000' and url != "/api/v2/spot/wallet/withdrawal": logger.warning(f'Response error "{url}": {r.text}')
        return r.json()
    except Exception as err:
        logger.error(f'response error with "{url}" {err}: {r.status_code} {r.reason} | {r.text}')
        return r.text


def get_headers(method: str, url: str, params: Optional[str] = ""):
    """
    method: "GET" or "POST"
    url: like ""
    """
    timestamp = str(int(time_ns() / 1000000))

    if params:
        if method.upper() == 'GET': params = '?' + "&".join([f"{key}={params[key]}" for key in params])
        elif method.upper() == "POST": params = dumps(params)

    to_sign = f'{timestamp}{method.upper()}{url}{params}'.encode("UTF-8")

    signed = hmac.new(settings.BITGET_SECRET.encode("UTF-8"), to_sign, sha256).digest()
    signed_encoded = b64encode(signed)

    return {
        'ACCESS-KEY': settings.BITGET_KEY,
        'ACCESS-SIGN': signed_encoded,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': settings.BITGET_PASSWORD,
        'Content-Type': 'application/json',
        'locale': 'en-US'
    }


def get_acc_info():
    response = send_request(
        method="GET",
        url='/api/v2/spot/account/info',
    )

    return response


def subacc_transfer(amount: float, coin: str, from_id: int):
    response = send_request(
        method="POST",
        url='/api/v2/spot/wallet/subaccount-transfer',
        payload={
            "fromType": "spot",
            "toType": "spot",
            "amount": amount,
            "coin": coin,
            "fromUserId": str(from_id),
            "toUserId": str(get_acc_info()['data']['userId']),
        }
    )

    if response['code'] != '00000':
        logger.error(f'Transfer {amount} {coin} error: {response}')
    return response['code'] == '00000'
