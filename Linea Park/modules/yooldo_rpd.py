from modules.utils import sleeping, logger
from modules.wallet import Wallet
import settings


class YooldoRPD(Wallet):
    def __init__(self, wallet: Wallet):
        super().__init__(privatekey=wallet.privatekey, recipient=wallet.recipient, db=wallet.db, browser=wallet.browser)

        self.from_chain = 'linea'
        self.web3 = self.get_web3(chain_name=self.from_chain)

        self.wait_for_gwei()
        self.rpd()


    def rpd(self, retry=0):
        try:
            module_str = f'yoldo rpd'

            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address('0x666a8f155e5c0316b0867f6ef5d410ae0fbcfbd8'),
                abi='[]'
            )

            contract_txn = {
                'from': self.address,
                'to': contract.address,
                'data': '0xab64d2e6',
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
                return self.rpd(retry=retry+1)
            else:
                if 'tx failed' not in str(error):
                    self.db.append_report(privatekey=self.privatekey, text=f'{module_str}: {error}', success=False)
                raise ValueError(f'{module_str}: {error}')
