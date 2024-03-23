from random import randint

from modules.utils import sleeping, logger
from modules.wallet import Wallet
import settings


class ReadOn(Wallet):
    def __init__(self, wallet: Wallet):
        super().__init__(privatekey=wallet.privatekey, recipient=wallet.recipient, db=wallet.db, browser=wallet.browser)

        self.from_chain = 'linea'
        self.web3 = self.get_web3(chain_name=self.from_chain)

        self.wait_for_gwei()
        self.curate()


    def curate(self, retry=0):
        try:
            module_str = f'readon (curate)'

            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address('0x8286d601a0ed6cf75E067E0614f73A5b9F024151'),
                abi='[{"inputs":[{"internalType":"uint64","name":"contentUrl","type":"uint64"}],"name":"curate","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
            )
            contract_txn = contract.functions.curate(randint(1710080500000000000, 1710080510000000000))

            tx_hash = self.sent_tx(chain_name=self.from_chain, tx=contract_txn, tx_label=module_str)
            return tx_hash

        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f'[-] Web3 | {module_str} | {error} [{retry + 1}/{settings.RETRY}]')
                sleeping(10)
                return self.curate(retry=retry+1)
            else:
                if 'tx failed' not in str(error):
                    self.db.append_report(privatekey=self.privatekey, text=f'{module_str}: {error}', success=False)
                raise ValueError(f'{module_str}: {error}')
