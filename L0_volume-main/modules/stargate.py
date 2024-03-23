import random
from modules.utils import sleeping, logger
from modules.wallet import Wallet
import settings
import time
from modules.const import (CHAINS_DATA, chain_w3, router_contract,
                           router_eth_contract, dstChainId, stg_contract, stargate_chain_ID, STG_address)


class Stargate(Wallet):
    def __init__(self, wallet: Wallet, from_chain, to_chain, router, full_bridge=False):
        super().__init__(privatekey=wallet.privatekey, recipient=wallet.recipient, recipient2=wallet.recipient2)

        if router==1:
            self.from_chain = from_chain
            self.to_chain = to_chain
            self.wait_for_gwei()
            self.CHAINS_DATA = CHAINS_DATA[from_chain]
            self.chain_w3 = chain_w3[from_chain]
            self.router_contract = router_contract[from_chain]
            self.router_eth_contract = router_eth_contract[from_chain]
            self.dstChainId = dstChainId[to_chain]

            self.bridge()
        else:
            self.full_bridge = full_bridge
            self.from_chain = from_chain
            self.to_chain = to_chain
            self.wait_for_gwei()
            self.CHAINS_DATA = CHAINS_DATA[from_chain]
            self.chain_w3 = chain_w3[from_chain]
            self.stg_contract = stg_contract[from_chain]
            self.dstChainId = stargate_chain_ID[to_chain]

            self.bridge_stg()

    def bridge(self, retry=0):
        try:
            min_eth_wallet = 0.001
            amount = round(random.uniform(settings.BRIDGE_VOLUME[0], settings.BRIDGE_VOLUME[1]) - min_eth_wallet, 7)

            if self.to_chain == 'arbitrum':#весь баланса из base бриджим
                amount = self.get_balance(chain_name=self.from_chain, human=True)-min_eth_wallet

            module_str = f'[•] Stargate bridge {self.from_chain} {amount} ETH to {self.to_chain}'
            logger.info(module_str)

            old_balance = self.get_balance(chain_name=self.to_chain, human=True)

            value_to_bridge = int(str(int(amount * 10 ** 18))[:6].ljust(len(str(int(amount * 10 ** 18)))-4, '0') + '9023')

            address = self.chain_w3.to_checksum_address(self.address)
            nonce = self.chain_w3.eth.get_transaction_count(address)
            gas_price = self.chain_w3.eth.gas_price

            fees = self.router_contract.functions.quoteLayerZeroFee(self.dstChainId, 1, address, "0x", [0, 0, address]).call()
            fee = fees[0]

            amountOutMin = value_to_bridge - (value_to_bridge * 5) // 1000

            swap_txn = self.router_eth_contract.functions.swapETH(
                self.dstChainId, address, address, value_to_bridge, amountOutMin
            ).build_transaction({
                'from': address,
                'value': value_to_bridge + fee,
                'gasPrice': gas_price,
                'nonce': nonce,
            })
            gasLimit = self.chain_w3.eth.estimate_gas(swap_txn)
            swap_txn['gas'] = int(gasLimit + gasLimit * 0.5)
            signed_swap_txn = self.chain_w3.eth.account.sign_transaction(swap_txn, self.privatekey)
            tx_hash = self.chain_w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)
            status = self.chain_w3.eth.wait_for_transaction_receipt(tx_hash, timeout=360).status
            if status == 1:
                self.wait_balance(chain_name=self.to_chain, needed_balance=old_balance, only_more=True)
                logger.success(f'{self.CHAINS_DATA["explorer"]}{tx_hash.hex()}')
                return tx_hash
            else:
                logger.error(f'[{address}] transaction failed!')
        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f'{error}')
                sleeping(10)
                return self.bridge(retry=retry+1)
            else:
                raise ValueError(f'{error}')

    def bridge_stg(self, retry=0):
        address = self.address
        stg_contract_ = self.stg_contract

        try:
            fee = self.fee_Stargate(self.from_chain, self.to_chain)
        except:
            logger.error(f'[{self.address}] не смог получить газ!', 'red')
            self.bridge_stg(retry+1)
            return False

        old_balance = self.get_balance(chain_name=self.to_chain, human=True, token_address=STG_address[self.to_chain])

        try:
            _dstChainId = self.dstChainId
            _to = self.chain_w3.to_checksum_address(address)

            _qty = round(random.uniform(settings.BRIDGE_VOLUME_STG[0], settings.BRIDGE_VOLUME_STG[1]))

            if self.from_chain != 'arbitrum':#весь баланса из base бриджим
                _qty = self.get_balance(chain_name=self.from_chain, human=True, token_address=STG_address[self.from_chain])
                if not self.full_bridge:
                    _qty = round(random.uniform(settings.BRIDGE_VOLUME_STG[0], _qty))
            _qty = int(_qty) * 10 ** 18
            zroPaymentAddress = '0x0000000000000000000000000000000000000000'
            adapterParam = '0x00010000000000000000000000000000000000000000000000000000000000014c08'

            gas_price = self.chain_w3.eth.gas_price
            swap_txn = stg_contract_.functions.sendTokens(
                _dstChainId, _to, _qty, zroPaymentAddress, adapterParam)
            swap_txn = swap_txn.build_transaction({
                'from': address,
                'value': fee,
                'gasPrice': gas_price,
                'nonce': self.chain_w3.eth.get_transaction_count(address),
            })
            gasLimit = self.chain_w3.eth.estimate_gas(swap_txn)
            swap_txn['gas'] = int(gasLimit + gasLimit * 0.5)
            signed_swap_txn = self.chain_w3.eth.account.sign_transaction(swap_txn, self.privatekey)
            tx_hash = self.chain_w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)
            status = self.chain_w3.eth.wait_for_transaction_receipt(tx_hash, timeout=360).status

            if status == 1:
                self.wait_balance(chain_name=self.to_chain, needed_balance=old_balance, only_more=True, token_address=STG_address[self.to_chain])
                logger.success(f'{self.CHAINS_DATA["explorer"]}{tx_hash.hex()}')
                return tx_hash
            else:
                logger.error(f'[{address}] transaction failed!')
        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f'{error}')
                sleeping(10)
                return self.bridge_stg(retry=retry + 1)
            else:
                raise ValueError(f'{error}')

    def fee_Stargate(self, from_chain, to_chain):
        contract = stg_contract[from_chain]
        popitka = 0
        fee = 0
        while popitka < 3 and fee == 0:
            popitka += 1
            try:
                if fee == 0:
                    fees = contract.functions.estimateSendTokensFee(stargate_chain_ID[to_chain], True, "0x").call()
                    fee = fees[0]
                    fee = fee * 110 // 100
                else:
                    return fee
            except:
                time.sleep(10)
                pass
        return fee
