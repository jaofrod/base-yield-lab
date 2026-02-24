import asyncio
import os
from dotenv import load_dotenv
from web3 import AsyncWeb3, WebSocketProvider
from eth_account import Account

load_dotenv()

ALCHEMY_WSS_URL = os.getenv("SEPOLIA_ALCHEMY_WSS_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

if not ALCHEMY_WSS_URL or not PRIVATE_KEY:
    raise ValueError("Env missing variables")

w3 = AsyncWeb3(WebSocketProvider(ALCHEMY_WSS_URL))
account = Account.from_key(PRIVATE_KEY)

async def send_eth(to_address: str, amount_eth: float, w3: AsyncWeb3):
    """Monta, assina e envia uma transação de ETH"""
    print(f"Sending {amount_eth} ETH to {to_address}...")

    # Valida o endereço de destino (sempre!)
    to_address_checksum = w3.to_checksum_address(to_address)

    # Converte o valor de ETH (float) para Wei (int)
    value_wei = w3.to_wei(amount_eth, 'ether')

    # Busca o Nonce atual direto da blockchain
    nonce = await w3.eth.get_transaction_count(account.address)

    # Garante que não estamos mandando pra rede errada
    chain_id = await w3.eth.chain_id

    # 21000 é o limite padrão exato para transferências simples de ETH
    gas = 21000 

    # O máximo que você aceita pagar por unidade de gas
    gas_price = await w3.eth.gas_price

    # Gorjeta para o minerador
    max_priority_fee = await w3.eth.max_priority_fee

    # Monta o dict da Transação
    tx_dict = {
        'chainId': chain_id,
        'nonce': nonce,
        'to': to_address_checksum,
        'value': value_wei,
        'gas': gas,
        'maxFeePerGas': gas_price,
        'maxPriorityFeePerGas': max_priority_fee
    }

    print("Assinando transação offline...")
    # 5. Assina com a Chave Privada (A mágica criptográfica acontece aqui)
    signed_tx = w3.eth.account.sign_transaction(tx_dict, private_key=PRIVATE_KEY)

    print("Enviando para a blockchain...")

    # 6. Faz o Broadcast para a rede
    try:
        tx_hash = await w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # O hash é o "comprovante" instantâneo de que a ordem foi pra fila
        print("\n✅ Transação enviada com sucesso!")
        print(f"🔗 Acompanhe no Etherscan: https://sepolia.etherscan.io/tx/{w3.to_hex(tx_hash)}")

        return w3.to_hex(tx_hash)

    except Exception as e:
        print(f"\n❌ Erro ao enviar transação: {e}")
        return None

async def start_w3(address, value):
    async with AsyncWeb3(WebSocketProvider(ALCHEMY_WSS_URL)) as w3:
        await send_eth(address, value, w3)

if __name__ == "__main__":
    DESTINO_TESTE = "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe" #Ethereum Foundation
    VALOR_TESTE = 0.0001

    asyncio.run(start_w3(DESTINO_TESTE, VALOR_TESTE))


