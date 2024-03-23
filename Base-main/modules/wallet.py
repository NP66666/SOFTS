from web3.middleware import geth_poa_middleware
from random import uniform
from typing import Union
from time import sleep
from web3 import Web3
import requests, hmac, base64

from modules.helper import logger, sleeping
import config
from config import proxy_server


class Wallet:
    def __init__(self, privatekey: str, recipient: str):
        self.privatekey = privatekey
        self.recipient = Web3().to_checksum_address(recipient)
        self.account = Web3().eth.account.from_key(privatekey)
        self.address = self.account.address
        self.max_retries = config.POVTOR_TX

    def get_web3(self, mainnet=False):
        if mainnet:
            web3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))
        else:
            web3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/base'))
            web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return web3

    def wait_for_gwei(self):
        first_check = True
        while True:
            new_gwei = round(self.get_web3(False).eth.gas_price / 10 ** 9, 2)
            if new_gwei < config.GWEI_CONTROL:
                if not first_check: 
                    logger.debug(f'[•] Web3 | New GWEI is {new_gwei}')
                break
            sleep(5)
            if first_check:
                first_check = False
                logger.debug(f'[•] Web3 | Waiting for GWEI at least {config.GWEI_CONTROL}. Now it is {new_gwei}')

    def get_gas(self):
        max_priority = self.get_web3().eth.max_priority_fee
        last_block = self.get_web3().eth.get_block('latest')
        base_fee = last_block['baseFeePerGas']
        block_filled = last_block['gasUsed'] / last_block['gasLimit'] * 100
        if block_filled > 50:
            base_fee *= 1.125
        if config.GWEI_MULTIPLIER > 1:
            base_fee *= config.GWEI_MULTIPLIER
        max_fee = int(base_fee + max_priority)

        return {'maxPriorityFeePerGas': max_fee, 'maxFeePerGas': max_fee}

    def sent_tx(self, tx, tx_label, tx_raw=False, value=0):
        try:
            web3 = self.get_web3()
            if not tx_raw:
                tx = tx.build_transaction({
                    'from': self.address,
                    'chainId': web3.eth.chain_id,
                    'nonce': web3.eth.get_transaction_count(self.address),
                    'value': value,
                    **self.get_gas(),
                })
                tx['gas'] = int(int(tx['gas']) * 1.1)

            signed_tx = web3.eth.account.sign_transaction(tx, self.privatekey)
            raw_tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash = web3.to_hex(raw_tx_hash)
            tx_link = f'https://basescan.org/tx/{tx_hash}'
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

    def get_balance(self, human=False):
        web3 = self.get_web3()
        while True:
            try:

                balance = web3.eth.get_balance(self.address)
                decimals = 18

                if not human: return balance
                return balance / 10 ** decimals
            except Exception as err:
                logger.warning(f'[•] Web3 | Get balance error: {err}')
                sleep(5)


    def wait_balance(self, chain_name: str, needed_balance: Union[int, float], only_more: bool = False):
        " needed_balance: human digit "

        token_name = 'ETH'
        if only_more: logger.debug(f'[•] Web3 | Waiting for balance more than {round(needed_balance, 6)} {token_name} in {chain_name.upper()}')
        else: logger.debug(f'[•] Web3 | Waiting for {round(needed_balance, 6)} {token_name} balance in {chain_name.upper()}')

        while True:
            try:
                new_balance = self.get_balance(human=True)

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

        proxies = {
            "http": proxy_server,
            "https": proxy_server,
        }

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

        amount_from = config.OKX_WITHDRAW_VALUES[0]
        amount_to = config.OKX_WITHDRAW_VALUES[1]
        wallet = self.address
        SUB_ACC = True
        SYMBOL = 'ETH'

        match chain:
            case 'base'     : CHAIN = 'Base'

        api_key = config.OKX_KEY
        secret_key = config.OKX_SECRET
        passphras = config.OKX_PASSWORD

        # take FEE for withdraw
        _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/currencies?ccy={SYMBOL}",
                                 meth="GET")
        response = requests.get(f"https://www.okx.cab/api/v5/asset/currencies?ccy={SYMBOL}", timeout=10,
                                headers=headers, proxies=proxies)

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
                                            headers=headers, proxies=proxies)
                    list_sub = list_sub.json()

                    for sub_data in list_sub['data']:
                        while True:
                            name_sub = sub_data['subAcct']

                            _, _, headers = okx_data(api_key, secret_key, passphras,
                                                     request_path=f"/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy={SYMBOL}",
                                                     meth="GET")
                            sub_balance = requests.get(
                                f"https://www.okx.cab/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy={SYMBOL}",
                                timeout=10, headers=headers, proxies=proxies)
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
                                                  timeout=10, headers=headers,proxies=proxies)
                            break

                try:
                    _, _, headers = okx_data(api_key, secret_key, passphras,
                                             request_path=f"/api/v5/account/balance?ccy={SYMBOL}")
                    balance = requests.get(f'https://www.okx.cab/api/v5/account/balance?ccy={SYMBOL}', timeout=10,
                                           headers=headers,proxies=proxies)
                    balance = balance.json()
                    balance = balance["data"][0]["details"][0]["cashBal"]

                    if balance != 0:
                        body = {"ccy": f"{SYMBOL}", "amt": float(balance), "from": 18, "to": 6, "type": "0",
                                "subAcct": "", "clientId": "", "loanTrans": "", "omitPosRisk": ""}
                        _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/transfer",
                                                 body=str(body), meth="POST")
                        a = requests.post("https://www.okx.cab/api/v5/asset/transfer", data=str(body), timeout=10,
                                          headers=headers,proxies=proxies)
                except Exception as ex:
                    pass

                # CHECK MAIN BALANCE
                _, _, headers = okx_data(api_key, secret_key, passphras,
                                         request_path=f"/api/v5/asset/balances?ccy={SYMBOL}", meth="GET")
                main_balance = requests.get(f'https://www.okx.cab/api/v5/asset/balances?ccy={SYMBOL}', timeout=10,
                                            headers=headers,proxies=proxies)
                main_balance = main_balance.json()
                main_balance = float(main_balance["data"][0]['availBal'])
                logger.info(f'[•] OKX | Total balance: {main_balance} {SYMBOL}')

                if amount_from > main_balance:
                    logger.warning(f'[•] OKX | Not enough balance ({main_balance} < {amount_from}), waiting 30 secs...')
                    sleep(30)
                    continue

                if amount_to > main_balance:
                    logger.warning(
                        f'[•] OKX | You want to withdraw MAX {amount_to} but have only {round(main_balance, 7)}')
                    amount_to = round(main_balance, 7)

                AMOUNT = round(uniform(amount_from, amount_to), 7)
                break

            old_balance = self.get_balance(human=True)

            body = {"ccy": SYMBOL, "amt": AMOUNT, "fee": FEE, "dest": "4", "chain": f"{SYMBOL}-{CHAIN}",
                    "toAddr": wallet}
            _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/withdrawal",
                                     meth="POST", body=str(body))
            a = requests.post("https://www.okx.cab/api/v5/asset/withdrawal", data=str(body), timeout=10,
                              headers=headers,proxies=proxies)
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

    def send_to(self, retry=0):

        try:
            web3 = self.get_web3()

            keep_values = round(uniform(config.BALANCE_VALUES[0], config.BALANCE_VALUES[1]), 7)

            balance = self.get_balance(human=True)
            amount = round(balance - keep_values, 6)
            if amount<0:
                logger.info(f'[Base] баланс меньше указанного')
                return
            value = int(amount * 10 ** 18)

            value = int(value - 21000 * web3.eth.gas_price * 1.1 // 10 ** 12 * 10 ** 12)  # round value
            amount = round(value / 10 ** 18, 5)

            module_str = f'sent {amount} ETH to {self.recipient}'

            tx = {
                'from': self.address,
                'to': self.recipient,
                'chainId': web3.eth.chain_id,
                'nonce': web3.eth.get_transaction_count(self.address),
                'value': value,
                #'gas': 1250000,
                **self.get_gas(),
            }
            gasLimit = web3.eth.estimate_gas(tx)
            tx['gas'] = int(gasLimit + gasLimit * 0.5)
            self.sent_tx(tx, module_str, tx_raw=True)

        except Exception as error:
            if retry < config.POVTOR_TX:
                logger.error(f'{error}')
                sleeping(10)
                return self.send_to(retry=retry + 1)
