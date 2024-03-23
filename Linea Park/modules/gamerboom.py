from modules.utils import sleeping, logger
from modules.wallet import Wallet
import settings


class Gamerboom(Wallet):
    def __init__(self, wallet: Wallet):
        super().__init__(privatekey=wallet.privatekey, recipient=wallet.recipient, db=wallet.db, browser=wallet.browser)

        self.from_chain = 'linea'
        self.web3 = self.get_web3(chain_name=self.from_chain)

        self.wait_for_gwei()
        self.proof()


    def proof(self, retry=0):
        try:
            module_str = f'gamerboom (proof)'

            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address('0x6CD20be8914A9Be48f2a35E56354490B80522856'),
                abi='[{"inputs":[],"name":"signGenesisProof","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
            )
            contract_txn = contract.functions.signGenesisProof()

            tx_hash = self.sent_tx(chain_name=self.from_chain, tx=contract_txn, tx_label=module_str)
            return tx_hash

        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f'[-] Web3 | {module_str} | {error} [{retry + 1}/{settings.RETRY}]')
                sleeping(10)
                return self.proof(retry=retry+1)
            else:
                if 'tx failed' not in str(error):
                    self.db.append_report(privatekey=self.privatekey, text=f'{module_str}: {error}', success=False)
                raise ValueError(f'{module_str}: {error}')
