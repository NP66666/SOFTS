from modules.utils import sleeping, logger
from modules.wallet import Wallet
import settings


class Zypher(Wallet):
    def __init__(self, wallet: Wallet):
        super().__init__(privatekey=wallet.privatekey, recipient=wallet.recipient, db=wallet.db, browser=wallet.browser)

        self.from_chain = 'linea'
        self.web3 = self.get_web3(chain_name=self.from_chain)

        self.wait_for_gwei()
        self.create_game()
        sleeping(settings.SLEEP_AFTER_TX)
        self.approve_nft()


    def create_game(self, retry=0):
        try:
            module_str = f'zypher2048 new game'

            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address('0x490d76b1e9418a78b5403740bd70dfd4f6007e0f'),
                abi='[{"inputs":[{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"bool","name":"reset","type":"bool"}],"name":"newGame","outputs":[],"stateMutability":"payable","type":"function"}]'
            )

            # contract_txn = contract.functions.newGame(
            #     int(''.join(choices(hexdigits, k=64)), 16),
            #     True
            # )

            contract_txn = {
                'from': self.address,
                'to': contract.address,
                'chainId': self.web3.eth.chain_id,
                'nonce': self.web3.eth.get_transaction_count(self.address),
                'value': 0,
                **self.get_gas(chain_name=self.from_chain),
            }
            contract_txn["gas"] = self.web3.eth.estimate_gas(contract_txn)

            tx_hash = self.sent_tx(chain_name=self.from_chain, tx=contract_txn, tx_label=module_str, tx_raw=True)
            return tx_hash

        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f'[-] Web3 | {module_str} | {error} [{retry + 1}/{settings.RETRY}]')
                sleeping(10)
                return self.create_game(retry=retry+1)
            else:
                if 'tx failed' not in str(error):
                    self.db.append_report(privatekey=self.privatekey, text=f'{module_str}: {error}', success=False)
                raise ValueError(f'{module_str}: {error}')


    def approve_nft(self, retry=0):
        try:
            module_str = f'zypher2048 approve nft'

            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address('0xa3ebaef88ef44b2b3d70ffd77e91cf002e5e72ce'),
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
