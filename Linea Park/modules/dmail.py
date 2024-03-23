from hashlib import sha256

from modules.utils import sleeping, logger
from modules.wallet import Wallet
import settings


class Dmail(Wallet):
    def __init__(self, wallet: Wallet):
        super().__init__(privatekey=wallet.privatekey, recipient=wallet.recipient, db=wallet.db, browser=wallet.browser)

        self.from_chain = 'linea'
        self.web3 = self.get_web3(chain_name=self.from_chain)

        self.wait_for_gwei()
        self.send_mail()


    def send_mail(self, retry=0):
        try:
            module_str = f'dmail message'

            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address('0xD1A3abf42f9E66BE86cfDEa8c5C2c74f041c5e14'),
                abi='[{"inputs":[{"internalType":"string","name":"to","type":"string"},{"internalType":"string","name":"path","type":"string"}],"name":"send_mail","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
            )
            send_to = self.web3.eth.account.create().address
            contract_txn = contract.functions.send_mail(
                sha256((self.address.lower() + '@dmail.ai').encode()).hexdigest(),
                sha256((send_to.lower() + '@dmail.ai').encode()).hexdigest()
            )

            tx_hash = self.sent_tx(chain_name=self.from_chain, tx=contract_txn, tx_label=module_str)
            return tx_hash

        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f'[-] Web3 | {module_str} | {error} [{retry + 1}/{settings.RETRY}]')
                sleeping(10)
                return self.send_mail(retry=retry+1)
            else:
                if 'tx failed' not in str(error):
                    self.db.append_report(privatekey=self.privatekey, text=f'{module_str}: {error}', success=False)
                raise ValueError(f'{module_str}: {error}')
