from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from eth_account.messages import encode_structured_data, encode_defunct
from random import uniform, random, randbytes, shuffle, choice
from ecdsa.keys import VerifyingKey, SigningKey
from ecdsa.curves import SECP256k1
from hashlib import sha512, sha256
from Crypto.Util.Padding import pad
from Crypto.Cipher import AES
from datetime import datetime
from base64 import b64encode
from eth_keys import keys
from time import time
from json import loads
import binascii
import hmac

from stark_lib.signature import get_hash_from_tx, sign, private_to_stark_key
from modules.utils import sleeping, logger
import config as config
from modules.wallet import Wallet


class Rhino(Wallet):
    def __init__(self, wallet: Wallet):
        super().__init__(privatekey=wallet.privatekey, browser=wallet.browser)

        if self.get_balance(chain_name='scroll', human=True) < config.SCROLL_MIN_BALANCE:
            self.choose_chain_from_bridge()

            self.web3 = self.get_web3(self.from_chain)
            self.wait_for_gwei()

            self.get_output_amount()
            tx_data = self.prepare_bridge()

            self.bridge(tx_data=tx_data)


    def choose_chain_from_bridge(self):
        rhino_chains = list(config.RHINO_BRIDGE_VALUES.keys())
        shuffle(rhino_chains)
        for chain in rhino_chains:
            chain_balance = self.get_balance(chain_name=chain, human=True)
            to_bridge_min = config.RHINO_BRIDGE_VALUES[chain][0]
            to_bridge_max = config.RHINO_BRIDGE_VALUES[chain][1]

            if chain_balance > to_bridge_min:
                if chain_balance < to_bridge_max:
                    to_bridge_max = chain_balance - 0.0004 # ~0.0004 bridge fee

                to_bridge = round(uniform(to_bridge_min, to_bridge_max), 5)
                self.from_chain = chain
                self.value = int(to_bridge * 10 ** 18)
                return True

    def create_auth(self):
        current_time = round(time(), 3)
        texted_time = datetime.utcfromtimestamp(current_time).strftime('%a, %d %b %Y %H:%M:%S GMT')

        text = f'''To protect your rhino.fi privacy we ask you to sign in with your wallet to see your data.
Signing in on {texted_time}. For your safety, only sign this message on rhino.fi!'''

        signature = self.web3.eth.account.sign_message(encode_defunct(text=text), private_key=self.privatekey).signature.hex()
        self.login_signature = signature
        self.login_current_time = f"v3-{current_time}"
        return 'EcRecover ' + b64encode(f'{{"signature":"{signature}","nonce":"v3-{current_time}"}}'.encode()).decode()


    def sign_eip712(self):
        challengeData = {"types":{"EIP712Domain":[{"name":"name","type":"string"},{"name":"version","type":"string"}],"rhino.fi":[{"type":"string","name":"action"},{"type":"string","name":"onlySignOn"}]},"domain":{"name":"rhino.fi","version":"1.0.0",},"primaryType":"rhino.fi","message":{"action":"Access your rhino.fi account","onlySignOn":"app.rhino.fi"}}
        message = encode_structured_data(challengeData)
        signed_message = self.web3.eth.account.sign_message(message, self.privatekey).signature.hex()
        hash_signed_msg = self.web3.keccak(text=signed_message).hex()
        return hash_signed_msg


    def decryptWithDTK(self, dtk: str, encryptedMessage: str):
        '''
        dtk: hash_signed_msg
        encryptedMessage: encryptedTradingKey
        '''

        def cipher_parse():
            buf = bytes.fromhex(encryptedMessage)

            parsedEncryptedMessage = {
                'iv': buf[0:16].hex(),
                'ephemPublicKey': buf[16:49].hex(),
                'mac': buf[49:81].hex(),
                'ciphertext': buf[81:].hex()
            }
            vk = VerifyingKey.from_string(bytes.fromhex(parsedEncryptedMessage['ephemPublicKey']), curve=SECP256k1)
            parsedEncryptedMessage['ephemPublicKey'] = vk.to_string('uncompressed').hex()
            return parsedEncryptedMessage


        def decryptWithPrivateKey(privateKey, encrypted):
            try:
                # derive(privateKey, encryptedBuffer["ephemPublicKey"])
                curve = SECP256k1
                key_a = SigningKey.from_string(bytes.fromhex(privateKey[2:]), curve=curve)                  # keyFromPrivate
                key_b = VerifyingKey.from_string(bytes.fromhex(encrypted["ephemPublicKey"]), curve=curve)   # keyFromPublic
                Px_ = key_a.privkey.secret_multiplier * key_b.pubkey.point
                Px = Px_.to_bytes().hex()[:64]
                hash = sha512(bytes.fromhex(Px)).hexdigest()

                # hmacSha256Verify(macKey, dataToMac, opts.mac)
                # pass

                # aesCbcDecrypt(opts.iv, encryptionKey, opts.ciphertext)
                cipher = Cipher(algorithms.AES(binascii.unhexlify(hash[:64])), modes.CBC(binascii.unhexlify(encrypted['iv'])),
                                backend=default_backend())
                decryptor = cipher.decryptor()
                decrypted_data = decryptor.update(binascii.unhexlify(encrypted['ciphertext'])) + decryptor.finalize()
                decrypted_data = decrypted_data.decode()
                try:
                    decrypted_data_to_json = decrypted_data[:decrypted_data.find('\x05')]
                    dtk = loads(decrypted_data_to_json)['data']
                except:
                    decrypted_data_to_json = decrypted_data[:decrypted_data.find('}')+1]
                    dtk = loads(decrypted_data_to_json)['data']
                return dtk
            except Exception as err:
                try:
                    logger.warning(f'decrypted_data: {decrypted_data}')
                except:
                    pass
                raise Exception(f'decryptWithPrivateKey error: {err}')


        parsedEncryptedMessage = cipher_parse()
        decrypted_tk = decryptWithPrivateKey(privateKey=dtk, encrypted=parsedEncryptedMessage)

        return decrypted_tk


    def get_output_amount(self):
        try:
            amount = round(self.value / 10 ** 18, 5)
            module_str = f'rhino bridge from {self.from_chain} {amount} ETH'

            self.receiveAmount = self.browser.get_rhino_bridge(auth=self.create_auth(), address=self.address, value=self.value)

            self.module_str = f'* rhino bridge from {self.from_chain} {amount} ETH -> scroll {self.receiveAmount} ETH'
        except Exception as err:
            raise Exception(f'{module_str} | error: {err}')


    def register_rhino(self):

        stark_privatekey = randbytes(32).hex()  # dtk
        eip_hash = self.sign_eip712() # encryptionKey
        public_key = str(keys.PrivateKey(self.web3.to_bytes(hexstr=eip_hash)).public_key)

        message = f'{{"data":"{stark_privatekey}"}}'.encode().hex()
        pubString = '04' + public_key.removeprefix('0x')
        ephemPrivateKey = randbytes(32).hex()

        signing_key = SigningKey.from_secret_exponent(int(ephemPrivateKey, 16), curve=SECP256k1, hashfunc=sha256)
        verifying_key = signing_key.get_verifying_key()
        ephemPublicKey = verifying_key.to_string('uncompressed').hex()

        key_a = SigningKey.from_string(bytes.fromhex(ephemPrivateKey), curve=SECP256k1)  # keyFromPrivate
        key_b = VerifyingKey.from_string(bytes.fromhex(pubString), curve=SECP256k1)  # keyFromPublic
        Px_ = key_a.privkey.secret_multiplier * key_b.pubkey.point
        Px = Px_.to_bytes().hex()[:64]
        hash = sha512(bytes.fromhex(Px)).hexdigest()

        iv = randbytes(16).hex()

        encryptionKey = hash[:64]
        macKey = hash[64:]

        cipher = AES.new(bytes.fromhex(encryptionKey), AES.MODE_CBC, iv=bytes.fromhex(iv))
        ciphertext = cipher.encrypt(pad(bytes.fromhex(message), AES.block_size)).hex()

        dataToMac = iv + ephemPublicKey + ciphertext

        key_bytes = bytes.fromhex(macKey)
        msg_bytes = bytes.fromhex(dataToMac)
        mac = hmac.new(key_bytes, msg_bytes, sha256).digest().hex()

        encrypted = {
            'iv': iv,
            'ephemPublicKey': ephemPublicKey,
            'ciphertext': ciphertext,
            'mac': mac,
        }

        compressedKey = '02' + encrypted['ephemPublicKey'][2:66]
        ret = bytes.fromhex(encrypted['iv']) + \
              bytes.fromhex(compressedKey) + \
              bytes.fromhex(encrypted['mac']) + \
              bytes.fromhex(encrypted['ciphertext'])
        encryptedMessage = ret.hex()

        coordinates = private_to_stark_key(stark_privatekey)

        stark_data = {"privateKey": coordinates['x'].removeprefix('0x').zfill(64), "dtk": encryptedMessage}
        self.browser.register(signature=self.login_signature, current_time=self.login_current_time, stark_data=stark_data)
        return stark_privatekey


    def registerStarkL1(self, stark_privatekey: str):
        # dvfStarkProvider.getPublicKey()
        coordinates = private_to_stark_key(stark_privatekey)
        stark_hex = coordinates['x'].removeprefix('0x').zfill(64)

        encoded_msg = '0x' + 'UserRegistration:'.encode().hex() + self.address.lower()[2:] + stark_hex
        hashed_msg = self.web3.solidity_keccak(['bytes'], [encoded_msg]).hex()
        ec_order = 3618502788666131213697322783095070105526743751716087489154079457884512865583
        message = hex(int(hashed_msg, 16) % ec_order)

        signed_msg = sign(msg_hash=message, priv_key=stark_privatekey)
        final = f'0x' \
                f'{signed_msg[0][2:].zfill(64)}' \
                f'{signed_msg[1][2:].zfill(64)}' \
                f'{coordinates["y"][2:].zfill(64)}'

        self.browser.starkL1Reg(signature=final)


    def prepare_bridge(self):
        devided_value = int(self.value / 10 ** 10)

        if not self.browser.getUserConf(address=self.address.lower()):
            logger.info(f'Registering in Rhino...')
            stark_privatekey = self.register_rhino()

            if not self.browser.registrations(address=self.address.lower()):
                logger.debug(f'Registering L1Stark...')
                self.registerStarkL1(stark_privatekey=stark_privatekey)


        encryptedTradingKey = self.browser.recoverTradingKey(address=self.address)
        hash_signed_msg = self.sign_eip712()
        decrypted_tk = self.decryptWithDTK(dtk=hash_signed_msg, encryptedMessage=encryptedTradingKey)

        vaultIdAndStarkKey = self.browser.vaultIdAndStarkKey()
        deposits_validate = self.browser.deposits_validate(value=devided_value)

        tx_data = {
            "amount": str(devided_value),
            "senderPublicKey": deposits_validate['starkKey'],
            "receiverPublicKey": vaultIdAndStarkKey['starkKey'],
            "receiverVaultId": vaultIdAndStarkKey['vaultId'],
            "senderVaultId": deposits_validate['vaultId'],
            "token": deposits_validate['tokenId'],
            "type": "TransferRequest",
            "nonce": round(random() * 2147483647),
            "expirationTimestamp": round((int(time()) + 180 * 24 * 60 * 60) / 60 / 60),
        }

        hash_from_tx = get_hash_from_tx(tx_data)

        r, s = sign(msg_hash=hash_from_tx, priv_key=decrypted_tk)
        tx_data.update({
            'signature': {
                'r': r,
                's': s,
            }
        })
        return tx_data


    def bridge(self, tx_data: dict, retry=0):
        try:
            module_str = '^ ' + self.module_str[2:]

            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(config.RHINO_CONTRACTS[self.from_chain]),
                abi='[{"inputs":[],"name":"depositNative","outputs":[],"stateMutability":"payable","type":"function"}]'
            )

            amount = round(self.value / 10 ** 18, 5)
            value_devided = int(self.value / 10 ** 10)
            module_str = f'rhino bridge from {self.from_chain} {amount} ETH -> scroll {self.receiveAmount} ETH'

            old_balance = self.get_balance(chain_name='scroll', human=True)

            contract_txn = contract.functions.depositNative()

            tx_hash = self.sent_tx(chain_name=self.from_chain, tx=contract_txn, tx_label=module_str, value=self.value)
            self.browser.create_bridge(tx_hash=tx_hash, value=value_devided, tx_data=tx_data, chain=self.from_chain)

            self.wait_balance(chain_name='scroll', needed_balance=old_balance, only_more=True)
            return tx_hash

        except Exception as error:
            if retry < config.RETRY and not 'Couldnt bridge on Rhino' in str(error):
                logger.error(f'{module_str} | {error}')
                sleeping(10)
                return self.bridge(tx_data=tx_data, retry=retry+1)
            else:
                raise ValueError(f'{module_str}: {error}')
