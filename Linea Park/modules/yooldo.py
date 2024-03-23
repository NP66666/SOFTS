from modules.utils import sleeping, logger
from modules.wallet import Wallet
import settings


class Yooldo(Wallet):
    def __init__(self, wallet: Wallet):
        super().__init__(privatekey=wallet.privatekey, recipient=wallet.recipient, db=wallet.db, browser=wallet.browser)

        self.from_chain = 'linea'
        self.web3 = self.get_web3(chain_name=self.from_chain)

        self.wait_for_gwei()
        self.checkin()


    def checkin(self, retry=0):
        try:
            module_str = f'yoldo (checkin)'

            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address('0x63ce21BD9af8CC603322cB025f26db567dE8102b'),
                abi='[{"type":"function","stateMutability":"payable","outputs":[],"name":"standUp","inputs":[]}]'
            )
            contract_txn = contract.functions.standUp()
            value = int(0.0001 * 1e18)

            tx_hash = self.sent_tx(chain_name=self.from_chain, tx=contract_txn, tx_label=module_str, value=value)
            return tx_hash

        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f'[-] Web3 | {module_str} | {error} [{retry + 1}/{settings.RETRY}]')
                sleeping(10)
                return self.checkin(retry=retry+1)
            else:
                if 'tx failed' not in str(error):
                    self.db.append_report(privatekey=self.privatekey, text=f'{module_str}: {error}', success=False)
                raise ValueError(f'{module_str}: {error}')
