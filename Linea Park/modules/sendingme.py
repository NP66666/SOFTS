from random import uniform
from eth_abi import encode

from modules.utils import sleeping, logger
from modules.wallet import Wallet
import settings


class SendingMe(Wallet):
    def __init__(self, wallet: Wallet):
        super().__init__(privatekey=wallet.privatekey, recipient=wallet.recipient, db=wallet.db, browser=wallet.browser)

        self.from_chain = 'linea'
        self.web3 = self.get_web3(chain_name=self.from_chain)

        self.wait_for_gwei()
        self.send()


    def send(self, retry=0):
        try:
            module_str = f'sending me'

            amount = round(uniform(settings.SENDING_ME_AMOUNT[0], settings.SENDING_ME_AMOUNT[1]), 8)
            value = int(amount * 1e18)
            module_str = f'sending me (send {amount} eth)'
            data = "0xf02bc6d5" + encode(["uint256", "address"], [int(0.0001 * 1e18), "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"]).hex()

            contract_txn = {
                'from': self.address,
                'to': self.web3.to_checksum_address('0x2933749E45796D50eBA9A352d29EeD6Fe58af8BB'),
                'value': value,
                'chainId': self.web3.eth.chain_id,
                'nonce': self.web3.eth.get_transaction_count(self.address),
                "data": data,
                **self.get_gas(chain_name=self.from_chain),
            }
            contract_txn["gas"] = self.web3.eth.estimate_gas(contract_txn)

            tx_hash = self.sent_tx(chain_name=self.from_chain, tx=contract_txn, tx_label=module_str, tx_raw=True)
            return tx_hash

        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f'[-] Web3 | {module_str} | {error} [{retry + 1}/{settings.RETRY}]')
                sleeping(10)
                return self.send(retry=retry+1)
            else:
                if 'tx failed' not in str(error):
                    self.db.append_report(privatekey=self.privatekey, text=f'{module_str}: {error}', success=False)
                raise ValueError(f'{module_str}: {error}')
