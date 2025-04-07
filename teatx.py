from web3 import Web3
import secrets
import random
import json
import time
import itertools
import threading
import sys

# Show credit splash
def show_credit():
    print("\n" + "="*40)
    print("🚀 Tea-TX by Altaffoc")
    print("="*40 + "\n")
    time.sleep(1)

# Load private key from .evm file
def load_private_key():
    with open(".evm", "r") as file:
        return file.read().strip()

# Connect to TEA Sepolia via Alchemy
RPC_URL = "https://tea-sepolia.g.alchemy.com/public"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Load wallet credentials
SENDER_ADDRESS = "0xSenderAddress" # Ganti Sender Add
PRIVATE_KEY = load_private_key()

# Input Token Details
def load_token_info():
    token_address = Web3.to_checksum_address(input("Enter Token Address: "))
    min_amount = float(input("Enter Min Token Amount: "))
    max_amount = float(input("Enter Max Token Amount: "))
    return token_address, min_amount, max_amount

TOKEN_ADDRESS, MIN_AMOUNT, MAX_AMOUNT = load_token_info()

# ERC-20 Token ABI
ERC20_ABI = json.loads('''
[
    {"constant":false,"inputs":[{"name":"recipient","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},
    {"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"}
]
''')

token_contract = web3.eth.contract(address=TOKEN_ADDRESS, abi=ERC20_ABI)

# Try to fetch the token name
try:
    TOKEN_NAME = token_contract.functions.name().call()
except Exception:
    TOKEN_NAME = "UnknownToken"

# Load recipient addresses from a file
def load_recipients():
    with open("recipients.txt", "r") as f:
        return [Web3.to_checksum_address(line.strip()) for line in f if line.strip()]

recipients = load_recipients()

# Spinner animation
def spinner():
    for c in itertools.cycle(['.', '..', '...']):
        if not waiting:
            break
        print(f'\r⏳ Waiting for new block{c} ', end='', flush=True)
        time.sleep(0.5)

# Send token transaction (with retry until success)
def send_token_transaction(to_address):
    success = False
    while not success:
        try:
            value = web3.to_wei(random.uniform(MIN_AMOUNT, MAX_AMOUNT), "ether")
            nonce = web3.eth.get_transaction_count(SENDER_ADDRESS)
            gas_price = web3.eth.gas_price * 2

            tx = token_contract.functions.transfer(to_address, value).build_transaction({
                "from": SENDER_ADDRESS,
                "nonce": nonce,
                "gas": 100000,
                "gasPrice": gas_price,
                "chainId": web3.eth.chain_id,
            })

            signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            print(f"\n✅ Success: Sent {web3.from_wei(value, 'ether')} {TOKEN_NAME} to {to_address} | TX: {tx_hash.hex()}")
            success = True
        except Exception:
            # Hide all errors silently and retry
            time.sleep(2)

# Monitor new blocks
def watch_new_blocks():
    global waiting
    latest_block = web3.eth.block_number
    print(f"🔎 Watching from Block {latest_block}")

    while recipients:
        new_block = web3.eth.block_number
        if new_block > latest_block:
            waiting = False
            print(f"\n📦 New Block: {new_block}")

            to_send = recipients.pop(0)
            send_token_transaction(to_send)

            latest_block = new_block
        else:
            waiting = True
            t = threading.Thread(target=spinner)
            t.start()
            while waiting:
                if web3.eth.block_number > latest_block:
                    waiting = False
                time.sleep(1)

# Run
if __name__ == "__main__":
    show_credit()
    waiting = False
    watch_new_blocks()
