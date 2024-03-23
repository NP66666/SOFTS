from modules.utils import sleeping, logger
from modules.wallet import Wallet
import settings


class SatoshiUniverse(Wallet):
    def __init__(self, wallet: Wallet):
        super().__init__(privatekey=wallet.privatekey, recipient=wallet.recipient, db=wallet.db, browser=wallet.browser)

        self.from_chain = 'linea'
        self.web3 = self.get_web3(chain_name=self.from_chain)

        self.wait_for_gwei()
        self.mint()


    def mint(self, retry=0):
        try:
            module_str = f'satoshi universe (mint nft)'

            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address('0xecbEE1a087aA83Db1fCC6C2C5eFFC30BCb191589'),
                abi='[{"inputs":[],"name":"fixedFee","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"to","type":"address"},{"internalType":"address","name":"collection","type":"address"},{"internalType":"uint24","name":"quantity","type":"uint24"},{"internalType":"bytes32[]","name":"merkleProof","type":"bytes32[]"},{"internalType":"uint8","name":"phaseId","type":"uint8"},{"internalType":"bytes","name":"payloadForCall","type":"bytes"}],"internalType":"structMintParams","name":"_params","type":"tuple"}],"name":"mint","outputs":[],"stateMutability":"payable","type":"function"}]'
            )

            fee = contract.functions.fixedFee().call()

            contract_txn = contract.functions.mint(
                (
                    self.address,
                    "0x0dE240B2A3634fCD72919eB591A7207bDdef03cd",
                    1,
                    [],
                    1,
                    "0x"
                )
            )

            tx_hash = self.sent_tx(chain_name=self.from_chain, tx=contract_txn, tx_label=module_str, value=fee)
            return tx_hash

        except Exception as error:
            if '!isAllowed' in str(error):
                logger.info(f'[+] Web3 | {module_str} already minted')
                self.db.append_report(privatekey=self.privatekey, text=f'{module_str} already minted', success=True)
            elif retry < settings.RETRY:
                logger.error(f'[-] Web3 | {module_str} | {error} [{retry + 1}/{settings.RETRY}]')
                sleeping(10)
                return self.mint(retry=retry+1)
            else:
                if 'tx failed' not in str(error):
                    self.db.append_report(privatekey=self.privatekey, text=f'{module_str}: {error}', success=False)
                raise ValueError(f'{module_str}: {error}')
