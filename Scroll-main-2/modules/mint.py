import requests
from web3 import Web3
from loguru import logger
from modules.helper import sing_and_chek_tx_legasy
from modules.abi_and_contract import NFT_ORIGINS_CONTRACT, NFT_ORIGINS_ABI


def get_nft_data(address):
    url = f"https://nft.scroll.io/p/{address}.json"

    response = requests.get(url=url)
    if response.status_code == 200:
        transaction_data = response.json()

        if "metadata" in transaction_data:
            return transaction_data["metadata"], transaction_data["proof"]
    return False, False


def mint(chain_w3, account, parametrs):
    logger.info(
        f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}][{account.address}] Mint nft')

    metadata, proof = get_nft_data(account.address)

    if not metadata or not proof:
        return logger.error(f"[{parametrs['current_account']}][{account.address}] Scroll Origins NFT Not Found")

    swap_txn = {
        "chainId": chain_w3.eth.chain_id,
        "from": account.address,
        "gasPrice": chain_w3.eth.gas_price,
        "nonce": chain_w3.eth.get_transaction_count(account.address),
    }
    contract = chain_w3.eth.contract(address=Web3.to_checksum_address(NFT_ORIGINS_CONTRACT), abi=NFT_ORIGINS_ABI)
    swap_txn = contract.functions.mint(
        account.address,
        (
            metadata.get("deployer"),
            metadata.get("firstDeployedContract"),
            metadata.get("bestDeployedContract"),
            int(metadata.get("rarityData", 0), 16),
        ),
        proof
    ).build_transaction(swap_txn)

    swap_txn.update({"gas": int(chain_w3.eth.estimate_gas(swap_txn) * 1.3)})
    success_tx, swap_txn_hash = sing_and_chek_tx_legasy(chain_w3, swap_txn, account)
    if success_tx:
        logger.info(f"https://scrollscan.com/tx/{swap_txn_hash.hex()}")
        logger.success(f'[{parametrs["current_account"]}/{parametrs["max_acconts"]}]'
                       f'[{account.address}] Successfully mint')
    else:
        logger.error(f'[{account.address}] enable error')