from modules.utils import sleeping, logger
from modules.wallet import Wallet
import settings


class Battlemon(Wallet):
    def __init__(self, wallet: Wallet):
        super().__init__(privatekey=wallet.privatekey, recipient=wallet.recipient, db=wallet.db, browser=wallet.browser)

        self.from_chain = 'linea'
        self.web3 = self.get_web3(chain_name=self.from_chain)

        self.wait_for_gwei()
        self.mint_nft()


    def mint_nft(self, retry=0):
        try:
            module_str = f'battlemon mint nft'

            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address('0x578705c60609c9f02d8b7c1d83825e2f031e35aa'),
                abi='[{"inputs":[],"name":"safeMint","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
            )

            contract_txn = contract.functions.safeMint()

            tx_hash = self.sent_tx(chain_name=self.from_chain, tx=contract_txn, tx_label=module_str)
            return tx_hash

        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f'[-] Web3 | {module_str} | {error} [{retry + 1}/{settings.RETRY}]')
                sleeping(10)
                return self.mint_nft(retry=retry+1)
            else:
                if 'tx failed' not in str(error):
                    self.db.append_report(privatekey=self.privatekey, text=f'{module_str}: {error}', success=False)
                raise ValueError(f'{module_str}: {error}')
