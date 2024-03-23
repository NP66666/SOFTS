from pyuseragents import random as random_ua
from random import random
from requests import Session
from time import sleep

from modules.utils import logger
import config


class Browser:
    def __init__(self):
        self.max_retries = 5
        self.session = Session()
        self.session.headers['user-agent'] = random_ua()
        if config.PROXY not in ['http://log:pass@ip:port', '']:
            self.change_ip()
            self.session.proxies.update({'http': config.PROXY, 'https': config.PROXY})
        #else:
            #logger.warning('You are not using proxy')


    def change_ip(self):
        if config.CHANGE_IP_LINK not in ['https://changeip.mobileproxy.space/?proxy_key=...&format=json', '']:
            while True:
                r = self.session.get(config.CHANGE_IP_LINK)
                if r.status_code == 200:
                    logger.info(f'[+] Proxy | Changed ip: {r.text}')
                    return True
                logger.warning(f'[•] Proxy | Change IP error: {r.text} | {r.status_code} {r.reason}')
                sleep(10)


    def get_rhino_bridge(self, auth: str, address: str, value: int):
        try:
            value = int(value / 10 ** 10)
            url = 'https://api.rhino.fi/v1/trading/withdrawalQuotes'
            params = {
                'token': 'ETH',
                'chain': 'SCROLL',
                'recipient': address.lower(),
                'amount': str(value),
                'type': 'BRIDGED',
            }
            self.session.headers.update({'Authorization': auth})

            r = self.session.get(url, params=params)
            receiveAmount = int(r.json()['receiveAmount'])
            if value - receiveAmount > config.MAX_DIFFERENCE * 10 ** 8:
                raise Exception(f'difference to high: {(value - receiveAmount) / 10 ** 8} ETH')

            return round(receiveAmount / 10 ** 8, 5)

        except Exception as err:
            raise Exception(f'Rhino Bridge quotes | {err}')


    def deposits_validate(self, value: int):
        try:
            url = 'https://api.rhino.fi/v1/trading/deposits-validate'
            payload = {
                "token": "ETH",
                "amount": str(value)
            }
            r = self.session.post(url, json=payload)

            return {'starkKey': r.json()['starkKey'], 'tokenId': r.json()['tokenId'], 'vaultId': r.json()['vaultId']}
        except Exception as err:
            logger.error(f'deposits_validate error: {err}')
            try: logger.debug(f'deposits_validate response: {r.text}')
            except: pass


    def vaultIdAndStarkKey(self):
        try:
            url = 'https://api.rhino.fi/v1/trading/r/vaultIdAndStarkKey'
            params = {
                "token": "ETH",
                "targetEthAddress": "0xaf8ae6955d07776ab690e565ba6fbc79b8de3a5d"
            }
            r = self.session.get(url, params=params)

            return {'starkKey': r.json()['starkKey'], 'vaultId': r.json()['vaultId']}
        except Exception as err:
            logger.error(f'vaultIdAndStarkKey error: {err}')
            try: logger.debug(f'vaultIdAndStarkKey response: {r.text}')
            except: pass


    def registrations(self, address: str):
        r = self.session.get(f'https://api.rhino.fi/v1/trading/registrations/{address}')
        if not r.json()['l1RegistrationSignature']: return False
        return True


    def starkL1Reg(self, signature: str):
        payload = {
            "l1RegistrationSignature": signature
        }
        url = 'https://api.rhino.fi/v1/trading/storeStarkL1Registration'
        r = self.session.post(url, json=payload)
        if r.json().get('status') == True:
            logger.success(f'L1Stark Registered')
        else:
            raise Exception(f'Rhino Stark Reg error: {r.text}')


    def getUserConf(self, address: str):
        r = self.session.post('https://api.rhino.fi/v1/trading/r/getUserConf')
        if r.json()['ethAddress'] and r.json()['ethAddress'] != address: raise Exception('getUserConf | addresses is different')
        return r.json()["isRegistered"]


    def register(self, signature: str, current_time: str, stark_data: dict):
        try:
            url = 'https://api.rhino.fi/v1/trading/w/register'
            payload = {
                "starkKey": stark_data['privateKey'],
                "encryptedTradingKey": {
                    "dtk": stark_data['dtk'],
                    "dtkVersion": "v3"
                },
                "nonce": current_time,
                "signature": signature,
                "meta": {
                    "walletType": "metamask",
                    "campaign": None,
                    "referer": None,
                    "platform": "DESKTOP"
                }
            }
            r = self.session.post(url, json=payload)
            if r.json()['isRegistered'] == True: logger.success(f'Successfully registered in Rhino!')
            else: raise Exception(f'not registered. response: {r.text}')

        except Exception as err:
            raise Exception(f'Rhino Register error: {err}')


    def recoverTradingKey(self, address: str):
        try:
            url = 'https://api.rhino.fi/v1/trading/r/recoverTradingKey'
            payload = {"ethAddress": address.lower()}
            r = self.session.post(url, json=payload)
            encryptedTradingKey = r.json()['encryptedTradingKey']
            if encryptedTradingKey: return r.json()['encryptedTradingKey']
            else: raise Exception('encryptedTradingKey is not created')
        except Exception as err:
            if not 'encryptedTradingKey is not created' in str(err):
                try: logger.debug(f'recoverTradingKey response: {r.text}')
                except: pass
            raise Exception(f'recoverTradingKey error: {err}')


    def create_bridge(self, tx_hash: str, value: int, tx_data: dict, chain: str):
        if chain == 'nova': chain = 'ARBITRUMNOVA'
        payload = {
            "chain": chain.upper(),
            "txHash": tx_hash,
            "token": "ETH",
            "amount": str(value),
            "bridge": {
                "token": "ETH",
                "chain": "SCROLL",
                "amount": str(value),
                "nonce": round(random() * 9007199254740991),
                "tx": tx_data
            }
        }
        url = 'https://api.rhino.fi/v1/trading/bridge'

        r = self.session.post(url, json=payload)

        if r.json().get('pending') == True:
            # logger.info('Successfully requested rhino bridge')
            return True
        else:
            logger.debug(f'response create_bridge: {r.status_code} {r.reason} | {r.text}')
            if 'Internal Server Error' in r.text:
                logger.debug(f'Internal Server Error Rhino Bridge error, trying again')
                sleep(5)
                return self.create_bridge(tx_hash=tx_hash, value=value, tx_data=tx_data, chain=chain)
            else:
                raise Exception(f'Couldnt bridge on Rhino, please visit site to withdraw funds manually.')
