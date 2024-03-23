from web3.middleware import geth_poa_middleware
from typing import Union
from time import sleep
from web3 import Web3
from modules.utils import logger
import config

class Wallet:
    def __init__(self, privatekey: str, browser):
        self.privatekey = privatekey
        self.account = Web3().eth.account.from_key(privatekey)
        self.address = self.account.address
        self.browser = browser

        self.max_retries = 5
        self.error = None


    def get_web3(self, chain_name: str):
        web3 = Web3(Web3.HTTPProvider(config.RPCS[chain_name]))
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return web3



    def wait_for_gwei(self):
        first_check = True
        while True:
            new_gwei = round(self.get_web3(chain_name='ethereum').eth.gas_price / 10 ** 9, 2)
            if new_gwei < config.GWEI_CONTROL:
                if not first_check: logger.debug(f'[•] Web3 | New GWEI is {new_gwei}')
                break
            sleep(5)
            if first_check:
                first_check = False
                logger.debug(f'[•] Web3 | Waiting for GWEI at least {config.GWEI_CONTROL}. Now it is {new_gwei}')


    def get_gas(self, chain_name):
        if chain_name in ['scroll', 'zksync']: return {'gasPrice': self.get_web3(chain_name=chain_name).eth.gas_price}
        max_priority = self.get_web3(chain_name=chain_name).eth.max_priority_fee
        last_block = self.get_web3(chain_name=chain_name).eth.get_block('latest')
        base_fee = last_block['baseFeePerGas']
        block_filled = last_block['gasUsed'] / last_block['gasLimit'] * 100
        if block_filled > 50: base_fee *= 1.125
        if config.GWEI_MULTIPLIER > 1: base_fee *= config.GWEI_MULTIPLIER
        max_fee = int(base_fee + max_priority)

        return {'maxPriorityFeePerGas': max_priority, 'maxFeePerGas': max_fee}

    def sent_tx(self, chain_name: str, tx, tx_label, tx_raw=False, value=0):
        try:
            web3 = self.get_web3(chain_name=chain_name)
            if not tx_raw:
                tx_to = tx.address
                tx = tx.build_transaction({
                    'from': self.address,
                    'chainId': web3.eth.chain_id,
                    'nonce': web3.eth.get_transaction_count(self.address),
                    'value': value,
                    **self.get_gas(chain_name=chain_name),
                })
                tx['gas'] = int(int(tx['gas']) * 1.1)
            else:
                try: tx_to = tx['to']
                except: tx_to = 'Null'

            signed_tx = web3.eth.account.sign_transaction(tx, self.privatekey)
            raw_tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash = web3.to_hex(raw_tx_hash)
            tx_link = f'{config.CHAINS_DATA[chain_name]["explorer"]}{tx_hash}'
            logger.debug(f'[•] Web3 | {tx_label} tx sent: {tx_link}')

            status = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=int(config.TIME_TO_WAIT * 60)).status

            if status == 1:
                logger.info(f'[+] Web3 | {tx_label} tx confirmed\n')
                return tx_hash
            else:
                raise ValueError(f'{tx_label} tx failed: {tx_link}')
        except Exception as err:
            try: encoded_tx = f'\n{tx._encode_transaction_data()}'
            except: encoded_tx = ''

            raise ValueError(f'failed: {err}{encoded_tx}')


    def get_balance(self, chain_name: str, token_name=False, human=False):
        web3 = self.get_web3(chain_name=chain_name)
        # if token_name:
        #     contract = web3.eth.contract(address=web3.to_checksum_address(config.TOKEN_ADDRESSES[token_name]),
        #                                  abi='[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]')
        while True:
            try:
                # if token_name: balance = contract.functions.balanceOf(self.address).call()
                # else: balance = web3.eth.get_balance(self.address)
                balance = web3.eth.get_balance(self.address)

                # decimals = contract.functions.decimals().call() if token_name else 18
                decimals = 18
                if not human: return balance
                return balance / 10 ** decimals
            except Exception as err:
                logger.warning(f'[•] Web3 | Get balance error: {err}')
                sleep(5)


    def wait_balance(self, chain_name: str, needed_balance: Union[int, float], only_more: bool = False):
        " needed_balance: human digit "
        if only_more: logger.debug(f'[•] Web3 | Waiting for balance more than {round(needed_balance, 6)} ETH in {chain_name.upper()}')
        else: logger.debug(f'[•] Web3 | Waiting for {round(needed_balance, 6)} ETH balance in {chain_name.upper()}')
        while True:
            try:
                new_balance = self.get_balance(chain_name=chain_name, human=True)
                if only_more: status = new_balance > needed_balance
                else: status = new_balance >= needed_balance
                if status:
                    logger.debug(f'[•] Web3 | New balance: {round(new_balance, 6)} ETH\n')
                    break
                sleep(5)
            except Exception as err:
                logger.warning(f'[•] Web3 | Wait balance error: {err}')
                sleep(10)




    def get_human_token_amount(self, value: Union[int, float], human=True):
        decimals = 18

        if human: return round(value / 10 ** decimals, 7)
        else: return int(value * 10 ** decimals)
