from modules.utils import sleeping, logger
from modules.wallet import Wallet
import settings


class Yuliverse(Wallet):
    def __init__(self, wallet: Wallet):
        super().__init__(privatekey=wallet.privatekey, recipient=wallet.recipient, db=wallet.db, browser=wallet.browser)

        self.from_chain = 'linea'
        self.web3 = self.get_web3(chain_name=self.from_chain)

        self.wait_for_gwei()
        self.approve_nft()


    def approve_nft(self, retry=0):
        try:
            module_str = f'yuliverse approve nft'

            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address('0x43264dCCF2bbFf0f21D711E46505c4c30879EAD2'),
                abi='[{"inputs":[{"internalType":"address","name":"address","type":"address"},{"internalType":"bool","name":"bool","type":"bool"}],"name":"setApprovalForAll","outputs":[],"stateMutability":"payable","type":"function"}]'
            )

            contract_txn = contract.functions.setApprovalForAll(
                self.web3.to_checksum_address("0x0caB6977a9c70E04458b740476B498B214019641"),
                True
            )

            tx_hash = self.sent_tx(chain_name=self.from_chain, tx=contract_txn, tx_label=module_str)
            return tx_hash

        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f'[-] Web3 | {module_str} | {error} [{retry + 1}/{settings.RETRY}]')
                sleeping(10)
                return self.approve_nft(retry=retry+1)
            else:
                if 'tx failed' not in str(error):
                    self.db.append_report(privatekey=self.privatekey, text=f'{module_str}: {error}', success=False)
                raise ValueError(f'{module_str}: {error}')
