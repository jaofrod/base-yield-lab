from web3 import Web3

API_KEY = "sTB6FuNoThM197hZCUEr8"
PROVIDER_URL = f"https://eth-mainnet.g.alchemy.com/v2/{API_KEY}"

w3 = Web3(Web3.HTTPProvider(PROVIDER_URL))

if w3.is_connected():
    print("Conectado à Blockchain!")

# wallets boas de espiar
# Vitalik Buterin: 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

raw_address = '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045'
checksum_address = Web3.to_checksum_address(raw_address)

# ouvindo a wallet selecionada
# wei é a menor unidade, tipo centavos dos centavos
# o balance vem em wei e dps convertemos para eth
balance_wei = w3.eth.get_balance(checksum_address)
balance_eth = w3.from_wei(balance_wei, 'ether')

print(f"O saldo da carteira {raw_address} é: {balance_eth} ETH")
