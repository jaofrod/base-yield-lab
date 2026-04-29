"""
executor.py — A Mao do bot. Executa transacoes na blockchain.

Fluxo para mover fundos entre protocolos (3 transacoes):
1. WITHDRAW do protocolo de origem (saca USDC de volta pra wallet)
2. APPROVE o protocolo de destino a gastar USDC da wallet
3. SUPPLY no protocolo de destino (deposita USDC)

CONCEITO: Por que 3 transacoes separadas?
Diferente de um banco onde voce faz uma transferencia direta, em DeFi
voce precisa:
1. Pedir pro protocolo A devolver seus tokens
2. Autorizar o protocolo B a pegar tokens da sua wallet (approve)
3. Pedir pro protocolo B pegar os tokens

Cada passo e uma transacao independente na blockchain, com seu proprio
hash e confirmacao. Se o passo 2 falhar, o USDC fica seguro na wallet.

CONCEITO: Paper Trading
Com PAPER_TRADING=true, o executor faz TUDO exceto enviar a transacao:
- Monta o objeto de transacao (valida que os parametros estao corretos)
- Assina com a chave privada (valida que a chave funciona)
- NAO chama send_raw_transaction (nao gasta gas real)
Isso permite testar o fluxo completo com dados reais da mainnet.
"""

import logging

from web3 import Web3
from eth_account import Account

from config import (
    BASE_RPC_URL,
    PRIVATE_KEY,
    PUBLIC_ADDRESS,
    CHAIN_ID,
    PAPER_TRADING,
    USDC_ADDRESS,
    AAVE_POOL_ADDRESS,
    COMPOUND_COMET_ADDRESS,
    USDC_ABI,
    AAVE_POOL_ABI,
    COMPOUND_COMET_ABI,
    USDC_DECIMALS,
    DEFAULT_GAS_LIMIT,
)
from state import LLMAction

logger = logging.getLogger(__name__)

# ============================================================
# SETUP
# ============================================================

w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
account = Account.from_key(PRIVATE_KEY)
wallet = Web3.to_checksum_address(PUBLIC_ADDRESS)

# Contratos
usdc_contract = w3.eth.contract(
    address=Web3.to_checksum_address(USDC_ADDRESS), abi=USDC_ABI
)
aave_pool = w3.eth.contract(
    address=Web3.to_checksum_address(AAVE_POOL_ADDRESS), abi=AAVE_POOL_ABI
)
compound_comet = w3.eth.contract(
    address=Web3.to_checksum_address(COMPOUND_COMET_ADDRESS), abi=COMPOUND_COMET_ABI
)


# ============================================================
# HELPERS
# ============================================================


def _usdc_to_raw(amount_float: float) -> int:
    """Converte USDC float (ex: 50.0) para unidades on-chain (ex: 50_000_000).

    CONCEITO: Decimais de tokens
    USDC tem 6 decimais. Entao 1 USDC = 1_000_000 unidades on-chain.
    A blockchain so trabalha com inteiros (uint256), nunca floats.
    Se voce enviar 50.0 direto, a transacao falha. Precisa enviar 50_000_000.
    """
    return int(amount_float * (10**USDC_DECIMALS))


def _build_and_send_tx(contract_call, description: str) -> dict:
    """Monta, assina e (opcionalmente) envia uma transacao.

    CONCEITO: Anatomia de uma transacao EVM
    - chainId: identifica a rede (8453 = Base). Evita replay attacks
      (alguem pegar sua TX assinada da Base e reenviar no Ethereum).
    - nonce: numero sequencial da wallet. Garante ordem e evita duplicatas.
    - gas: limite maximo de gas que a TX pode consumir. Sobra e refundada.
    - maxFeePerGas: preco maximo por unidade de gas que voce aceita pagar.
    - maxPriorityFeePerGas: "gorjeta" pro validador priorizar sua TX.

    Em paper mode: monta e assina (valida estrutura), mas NAO envia.
    """
    nonce = w3.eth.get_transaction_count(wallet)
    gas_price = w3.eth.gas_price
    max_priority_fee = w3.eth.max_priority_fee

    tx = contract_call.build_transaction({
        "chainId": CHAIN_ID,
        "from": wallet,
        "nonce": nonce,
        "gas": DEFAULT_GAS_LIMIT,
        "maxFeePerGas": gas_price + max_priority_fee,
        "maxPriorityFeePerGas": max_priority_fee,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)

    if PAPER_TRADING:
        logger.info(f"[PAPER] {description} — TX montada e assinada (nao enviada)")
        logger.info(f"[PAPER]   nonce={nonce}, gas={DEFAULT_GAS_LIMIT}, gasPrice={gas_price}")
        return {
            "status": "paper",
            "description": description,
            "nonce": nonce,
            "tx_hash": "0x_paper_" + description.replace(" ", "_")[:20],
        }

    # --- MODO REAL: enviar para a blockchain ---
    logger.info(f"Enviando TX: {description}...")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_hash_hex = w3.to_hex(tx_hash)
    logger.info(f"TX enviada: {tx_hash_hex}")

    # Esperar confirmacao (timeout 120s)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    if receipt["status"] == 1:
        logger.info(f"TX confirmada: {tx_hash_hex} (block {receipt['blockNumber']})")
        return {
            "status": "success",
            "description": description,
            "tx_hash": tx_hash_hex,
            "block": receipt["blockNumber"],
            "gas_used": receipt["gasUsed"],
        }
    else:
        logger.error(f"TX REVERTIDA: {tx_hash_hex}")
        return {
            "status": "reverted",
            "description": description,
            "tx_hash": tx_hash_hex,
        }


# ============================================================
# OPERACOES POR PROTOCOLO
# ============================================================


def _withdraw_from_aave(amount_raw: int) -> dict:
    """Saca USDC do Aave V3.

    CONCEITO: withdraw(asset, amount, to)
    - asset: endereco do token (USDC)
    - amount: quanto sacar. Use 2^256-1 para sacar TUDO
    - to: para onde enviar os tokens (nossa wallet)

    O Aave "queima" os aTokens correspondentes e transfere USDC pra wallet.
    """
    usdc = Web3.to_checksum_address(USDC_ADDRESS)
    call = aave_pool.functions.withdraw(usdc, amount_raw, wallet)
    return _build_and_send_tx(call, f"withdraw {amount_raw} USDC from Aave")


def _withdraw_from_compound(amount_raw: int) -> dict:
    """Saca USDC do Compound III.

    CONCEITO: withdraw(asset, amount)
    Compound III e mais simples — so precisa do token e valor.
    O contrato debita do seu saldo interno e transfere USDC pra wallet.
    """
    usdc = Web3.to_checksum_address(USDC_ADDRESS)
    call = compound_comet.functions.withdraw(usdc, amount_raw)
    return _build_and_send_tx(call, f"withdraw {amount_raw} USDC from Compound")


def _approve_usdc(spender_address: str, amount_raw: int) -> dict:
    """Aprova um contrato a gastar USDC da nossa wallet.

    CONCEITO: ERC-20 approve
    Antes de depositar tokens num contrato DeFi, voce PRECISA autorizar
    aquele contrato a "puxar" tokens da sua wallet. E uma medida de
    seguranca do padrao ERC-20.

    Sem approve, a TX de supply/deposit falha com "insufficient allowance".

    Normalmente se aprova o valor exato (nao um valor infinito), por seguranca.
    Se um contrato for hackeado e voce aprovou infinito, o hacker pode drenar
    todos os seus tokens. Aprovando o valor exato, no maximo ele leva aquele valor.
    """
    spender = Web3.to_checksum_address(spender_address)
    call = usdc_contract.functions.approve(spender, amount_raw)
    return _build_and_send_tx(call, f"approve {amount_raw} USDC for {spender_address[:10]}...")


def _supply_to_aave(amount_raw: int) -> dict:
    """Deposita USDC no Aave V3.

    CONCEITO: supply(asset, amount, onBehalfOf, referralCode)
    - asset: token a depositar (USDC)
    - amount: quanto depositar
    - onBehalfOf: quem recebe os aTokens (nossa wallet)
    - referralCode: sistema de afiliados do Aave (0 = nenhum)

    Apos supply, voce recebe aUSDC na wallet. Seu saldo de aUSDC
    cresce automaticamente com os juros.
    """
    usdc = Web3.to_checksum_address(USDC_ADDRESS)
    call = aave_pool.functions.supply(usdc, amount_raw, wallet, 0)
    return _build_and_send_tx(call, f"supply {amount_raw} USDC to Aave")


def _supply_to_compound(amount_raw: int) -> dict:
    """Deposita USDC no Compound III.

    CONCEITO: supply(asset, amount)
    Compound III registra o deposito internamente. Nao recebe token extra.
    Seu balanceOf() no contrato ja reflete o deposito + juros.
    """
    usdc = Web3.to_checksum_address(USDC_ADDRESS)
    call = compound_comet.functions.supply(usdc, amount_raw)
    return _build_and_send_tx(call, f"supply {amount_raw} USDC to Compound")


# ============================================================
# FUNCAO PUBLICA: execute_action()
# ============================================================


def execute_action(action: LLMAction) -> dict:
    """Executa uma acao de movimentacao de fundos.

    Fluxo completo:
    1. Determinar origem e destino
    2. Sacar do protocolo de origem (withdraw)
    3. Aprovar o protocolo de destino (approve)
    4. Depositar no protocolo de destino (supply)

    Se qualquer passo falhar, para e retorna o erro.
    O USDC fica seguro na wallet entre os passos.

    Retorna dict com status e detalhes de cada TX.
    """
    if action.action != "move_funds":
        return {"status": "skipped", "reason": f"action is {action.action}, not move_funds"}

    amount = action.amount_usdc
    # -1 significa "mover tudo" — o caller precisa resolver o valor real
    # Mas por seguranca, se chegar aqui com -1, usamos o balance
    if amount <= 0:
        return {"status": "error", "reason": "amount must be > 0 (resolve -1 before calling executor)"}

    amount_raw = _usdc_to_raw(amount)
    results = []

    mode = "PAPER" if PAPER_TRADING else "LIVE"
    logger.info(f"[{mode}] Executando: {action.from_protocol} -> {action.to_protocol} | {amount} USDC")

    # --- PASSO 1: Withdraw do protocolo de origem ---
    if action.from_protocol == "aave_v3":
        result = _withdraw_from_aave(amount_raw)
        results.append(result)
        if result["status"] == "reverted":
            return {"status": "error", "step": "withdraw", "results": results}

    elif action.from_protocol == "compound_iii":
        result = _withdraw_from_compound(amount_raw)
        results.append(result)
        if result["status"] == "reverted":
            return {"status": "error", "step": "withdraw", "results": results}

    elif action.from_protocol == "wallet":
        # USDC ja esta na wallet, nao precisa sacar
        logger.info("USDC ja esta na wallet, pulando withdraw")
    else:
        return {"status": "error", "reason": f"from_protocol desconhecido: {action.from_protocol}"}

    # --- PASSO 2: Approve USDC para o protocolo de destino ---
    if action.to_protocol == "aave_v3":
        spender = AAVE_POOL_ADDRESS
    elif action.to_protocol == "compound_iii":
        spender = COMPOUND_COMET_ADDRESS
    else:
        return {"status": "error", "reason": f"to_protocol desconhecido: {action.to_protocol}"}

    result = _approve_usdc(spender, amount_raw)
    results.append(result)
    if result["status"] == "reverted":
        return {"status": "error", "step": "approve", "results": results}

    # --- PASSO 3: Supply no protocolo de destino ---
    if action.to_protocol == "aave_v3":
        result = _supply_to_aave(amount_raw)
    elif action.to_protocol == "compound_iii":
        result = _supply_to_compound(amount_raw)

    results.append(result)
    if result["status"] == "reverted":
        return {"status": "error", "step": "supply", "results": results}

    logger.info(f"[{mode}] Movimentacao completa: {len(results)} TXs executadas")
    return {"status": "success", "results": results}
