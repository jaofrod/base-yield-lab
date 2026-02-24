import asyncio
from web3 import AsyncWeb3, WebSocketProvider
from web3.datastructures import AttributeDict
from dotenv import load_dotenv
import os

load_dotenv()

ALCHEMY_WSS_URL = os.getenv("SEPOLIA_ALCHEMY_WSS_URL")
ADDRESS = os.getenv("PUBLIC_ADDRESS")

if not ALCHEMY_WSS_URL or not ADDRESS:
    raise ValueError("Env missing variables")

address_checksum = AsyncWeb3.to_checksum_address(ADDRESS)

async def scan_block_for_deposits(block_number, w3: AsyncWeb3):
    """Busca um bloco específico e verifica todas as transações dele"""

    try:
        await asyncio.sleep(1)

        block = await w3.eth.get_block(block_number, full_transactions=True)

        transactions = block.get('transactions', [])

        for tx in transactions:
            if isinstance(tx, (dict, AttributeDict)):
                tx_to = tx.get('to')

                if tx_to == address_checksum:
                    value = tx.get('value', 0)
                    tx_from = tx.get('from', 'Unknown')
                    tx_hash = tx.get('hash')
                    value_eth = w3.from_wei(value, 'ether')

                    print("\n" + "="*50)
                    print("deposit detected")
                    print(f"from: {tx_from}")
                    print(f"to: {tx_to}")
                    print(f"value: {value_eth} ETH")
                    if tx_hash:
                        print(f"Hash: {tx_hash.hex()}")
                    print("="*50 + "\n")

    except Exception as e:
        print(f"Error processing block {block_number}: {e}")


async def listen_to_new_blocks():
    """Abre a conexão WebSocket e fica escutando novos blocos eternamente"""
    print(f"Starting Web3 listener for: {address_checksum}")
    print("waiting for new blocks (~12 seconds on Ethereum)...")

    async with AsyncWeb3(WebSocketProvider(ALCHEMY_WSS_URL)) as w3:
        # Cria uma assinatura (subscription) para novos cabeçalhos de blocos
        subscription_id = await w3.eth.subscribe('newHeads')

        # Loop de eventos assíncrono para processar as mensagens do WebSocket
        async for message in w3.socket.process_subscriptions():
            if message:
                # O payload retorna um JSON com os dados do novo bloco
                block_number = message['result']['number']

                # Dispara a varredura do bloco sem travar o loop de escuta
                asyncio.create_task(scan_block_for_deposits(block_number, w3))

if __name__ == "__main__":
    try:
       asyncio.run(listen_to_new_blocks())
    except KeyboardInterrupt:
        print("\nbye bye...")
    except Exception as e:
        print(f"error: {e}")

