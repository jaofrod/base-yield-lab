"""
listener.py — O Olho do bot. Le dados on-chain da Base mainnet.

A cada ciclo, faz chamadas RPC (via Alchemy) para ler:
- APY do Aave V3 e Compound III
- Saldos do bot em cada protocolo
- Saldo USDC e ETH livres na wallet
- Gas price atual

CONCEITO: RPC (Remote Procedure Call)
Voce nao roda um node da blockchain no seu computador. Em vez disso,
usa um servico como Alchemy que roda nodes e expoe uma API HTTP.
Cada chamada de funcao de um contrato e uma "eth_call" — voce envia
o endereco do contrato + dados codificados, e o node retorna o resultado.
Isso e gratuito para funcoes "view" (que so leem dados, nao mudam estado).

CONCEITO: Sync vs Async
Para polling a cada 5 minutos, HTTP sincrono e mais simples e confiavel
que WebSocket assincrono. WebSocket faz sentido para reagir em tempo real
(ex: detectar uma TX no mempool), mas nosso bot nao precisa disso.
"""

import logging
import time

from web3 import Web3

from config import (
    BASE_RPC_URL,
    PUBLIC_ADDRESS,
    CHAIN_ID,
    USDC_ADDRESS,
    AAVE_POOL_ADDRESS,
    AAVE_DATA_PROVIDER_ADDRESS,
    COMPOUND_COMET_ADDRESS,
    USDC_ABI,
    AAVE_POOL_ABI,
    AAVE_DATA_PROVIDER_ABI,
    COMPOUND_COMET_ABI,
    RAY,
    SECONDS_PER_YEAR,
    USDC_DECIMALS,
    DEFAULT_GAS_LIMIT,
    ETH_PRICE_USD,
    MIN_APY_DIFF,
    MIN_APY_ABSOLUTE,
)
from state import (
    BotState,
    NetworkState,
    WalletState,
    ProtocolPosition,
    ComputedState,
    HistoryState,
    load_history,
)

logger = logging.getLogger(__name__)

# ============================================================
# CONEXAO E CONTRATOS
# ============================================================

w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))

# Instanciar objetos de contrato
# CONCEITO: Contract object
# web3.py cria um objeto Python que "mapeia" as funcoes da ABI
# para metodos Python. Assim, em vez de codificar bytes manualmente,
# voce chama contrato.functions.balanceOf(endereco).call()
usdc_contract = w3.eth.contract(
    address=Web3.to_checksum_address(USDC_ADDRESS), abi=USDC_ABI
)
aave_pool = w3.eth.contract(
    address=Web3.to_checksum_address(AAVE_POOL_ADDRESS), abi=AAVE_POOL_ABI
)
aave_data_provider = w3.eth.contract(
    address=Web3.to_checksum_address(AAVE_DATA_PROVIDER_ADDRESS),
    abi=AAVE_DATA_PROVIDER_ABI,
)
compound_comet = w3.eth.contract(
    address=Web3.to_checksum_address(COMPOUND_COMET_ADDRESS),
    abi=COMPOUND_COMET_ABI,
)

wallet = Web3.to_checksum_address(PUBLIC_ADDRESS)
usdc_checksum = Web3.to_checksum_address(USDC_ADDRESS)


# ============================================================
# FUNCOES DE LEITURA ON-CHAIN
# ============================================================


def get_aave_apy() -> float:
    """Le o APY atual do Aave V3 para USDC.

    CONCEITO: getReserveData
    Retorna um "tuple" gigante com toda informacao do mercado USDC no Aave.
    O campo que nos interessa e currentLiquidityRate — a taxa anualizada
    que depositantes recebem, em "ray" (1e27 = 100%).

    Exemplo: liquidityRate = 3e25 → 3e25 / 1e27 = 0.03 = 3% APY
    """
    reserve_data = aave_pool.functions.getReserveData(usdc_checksum).call()
    # reserve_data e uma tupla. currentLiquidityRate e o indice 2
    liquidity_rate = reserve_data[2]
    apy = (liquidity_rate / RAY) * 100
    return apy


def get_compound_apy() -> float:
    """Le o APY atual do Compound III para USDC.

    CONCEITO: Utilization → Supply Rate
    Compound III calcula o APY em dois passos:
    1. getUtilization() → quanto do capital depositado esta emprestado (0-1e18)
    2. getSupplyRate(utilization) → taxa por SEGUNDO que depositantes ganham

    Para converter taxa-por-segundo em APY anual:
    APY = ((1 + rate_per_second) ^ seconds_per_year) - 1

    Isso e juros compostos! Cada segundo, voce ganha juros sobre juros.
    Na pratica, pra taxas pequenas, e quase igual a rate * seconds_per_year.
    """
    utilization = compound_comet.functions.getUtilization().call()
    supply_rate = compound_comet.functions.getSupplyRate(utilization).call()
    rate_per_second = supply_rate / 1e18
    apy = ((1 + rate_per_second) ** SECONDS_PER_YEAR - 1) * 100
    return apy


def get_aave_balance() -> float:
    """Le quanto USDC o bot tem depositado no Aave.

    CONCEITO: getUserReserveData
    O PoolDataProvider do Aave retorna os dados do usuario para um ativo
    especifico. O primeiro campo (currentATokenBalance) ja inclui juros
    acumulados — e o saldo "real" que voce receberia se sacasse agora.
    """
    result = aave_data_provider.functions.getUserReserveData(
        usdc_checksum, wallet
    ).call()
    # currentATokenBalance e o indice 0
    raw_balance = result[0]
    return raw_balance / (10**USDC_DECIMALS)


def get_compound_balance() -> float:
    """Le quanto USDC o bot tem depositado no Compound III.

    CONCEITO: balanceOf no Compound III
    Diferente do Aave (que te da um token aUSDC separado), o Compound
    rastreia seu saldo internamente. balanceOf() ja retorna saldo + juros.
    Sem token extra na sua wallet.
    """
    raw_balance = compound_comet.functions.balanceOf(wallet).call()
    return raw_balance / (10**USDC_DECIMALS)


def get_wallet_usdc_balance() -> float:
    """Le quanto USDC livre o bot tem na wallet (nao depositado em nenhum protocolo)."""
    raw_balance = usdc_contract.functions.balanceOf(wallet).call()
    return raw_balance / (10**USDC_DECIMALS)


def get_wallet_eth_balance() -> float:
    """Le quanto ETH o bot tem na wallet (para pagar gas).

    CONCEITO: Wei → ETH
    1 ETH = 10^18 Wei. Wei e a menor unidade, como centavos sao pro real.
    web3.py retorna saldos em Wei, entao convertemos dividindo por 10^18.
    """
    raw_balance = w3.eth.get_balance(wallet)
    return w3.from_wei(raw_balance, "ether")


def get_gas_price_gwei() -> float:
    """Le o gas price atual da rede Base em Gwei.

    CONCEITO: Gwei
    1 ETH = 10^9 Gwei. Gas price e medido em Gwei porque e mais legivel.
    Na Base (L2), gas price e tipicamente 0.001-0.01 Gwei — muito barato.
    """
    gas_price_wei = w3.eth.gas_price
    return float(w3.from_wei(gas_price_wei, "gwei"))


# ============================================================
# FUNCAO PUBLICA: build_state()
# ============================================================


def build_state() -> BotState:
    """Monta o estado completo do bot lendo dados on-chain.

    Esta e a UNICA funcao publica do listener. Ela:
    1. Faz todas as chamadas RPC
    2. Calcula valores derivados (melhor protocolo, diferenca de APY, etc)
    3. Carrega historico do disco
    4. Retorna um BotState pronto para o engine consumir
    """
    logger.info("Lendo dados on-chain da Base...")

    # --- Leituras on-chain (cada uma e uma chamada RPC) ---
    aave_apy = get_aave_apy()
    compound_apy = get_compound_apy()
    aave_balance = get_aave_balance()
    compound_balance = get_compound_balance()
    wallet_usdc = get_wallet_usdc_balance()
    wallet_eth = get_wallet_eth_balance()
    gas_price = get_gas_price_gwei()
    block_number = w3.eth.block_number

    # --- Network state ---
    # Custo estimado de gas em USD para uma operacao completa (3 TXs)
    # Formula: gas_limit * gas_price_wei * 3 / 10^18 * ETH_PRICE_USD
    gas_price_wei = w3.eth.gas_price
    gas_cost_usd = (DEFAULT_GAS_LIMIT * gas_price_wei * 3) / 1e18 * ETH_PRICE_USD

    network = NetworkState(
        chain_id=CHAIN_ID,
        gas_price_gwei=gas_price,
        gas_cost_estimate_usd=gas_cost_usd,
        block_number=block_number,
    )

    # --- Wallet state ---
    wallet_state = WalletState(
        address=PUBLIC_ADDRESS,
        usdc_balance=wallet_usdc,
        eth_balance=float(wallet_eth),
    )

    # --- Protocol positions ---
    aave_pos = ProtocolPosition(deposited_usdc=aave_balance, current_apy_pct=aave_apy)
    compound_pos = ProtocolPosition(deposited_usdc=compound_balance, current_apy_pct=compound_apy)

    # --- Computed state ---
    total_capital = aave_balance + compound_balance + wallet_usdc

    # Determinar onde esta o capital e qual protocolo e melhor
    if aave_balance > compound_balance:
        current_protocol = "aave_v3"
        current_apy = aave_apy
    elif compound_balance > aave_balance:
        current_protocol = "compound_iii"
        current_apy = compound_apy
    else:
        current_protocol = "none"
        current_apy = 0.0

    if aave_apy > compound_apy:
        best_protocol = "aave_v3"
        best_apy = aave_apy
    else:
        best_protocol = "compound_iii"
        best_apy = compound_apy

    apy_diff = abs(aave_apy - compound_apy)

    # Deveria considerar mover? Sim se:
    # 1. Diferenca de APY >= threshold
    # 2. O melhor protocolo NAO e onde o capital ja esta
    # 3. O melhor APY esta acima do minimo absoluto
    should_move = (
        apy_diff >= MIN_APY_DIFF
        and best_protocol != current_protocol
        and best_apy >= MIN_APY_ABSOLUTE
    )

    # Estimativa de ganho anual se mover (em USD)
    annual_gain = (apy_diff / 100) * total_capital

    computed = ComputedState(
        total_capital_usdc=total_capital,
        best_protocol=best_protocol,
        best_apy_pct=best_apy,
        current_protocol=current_protocol,
        current_apy_pct=current_apy,
        apy_diff_pct=apy_diff,
        should_consider_move=should_move,
        estimated_annual_gain_if_move=annual_gain,
        estimated_gas_cost_for_move=gas_cost_usd,
    )

    # --- History ---
    history = load_history()

    state = BotState(
        timestamp=time.time(),
        network=network,
        wallet=wallet_state,
        aave=aave_pos,
        compound=compound_pos,
        computed=computed,
        history=history,
    )

    return state


# ============================================================
# STANDALONE: rodar sozinho para testar leitura de dados
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

    if not w3.is_connected():
        print("ERRO: Nao conseguiu conectar na Base via RPC")
        print(f"URL: {BASE_RPC_URL[:50]}...")
        exit(1)

    print(f"Conectado na Base! Chain ID: {w3.eth.chain_id}")
    print(f"Wallet: {PUBLIC_ADDRESS}")
    print()

    state = build_state()

    print("\n=== ESTADO ATUAL ===")
    print(f"Aave APY:      {state.aave.current_apy_pct:.4f}%")
    print(f"Compound APY:  {state.compound.current_apy_pct:.4f}%")
    print(f"Diferenca:     {state.computed.apy_diff_pct:.4f}%")
    print(f"Melhor:        {state.computed.best_protocol}")
    print()
    print(f"Aave balance:    {state.aave.deposited_usdc:.6f} USDC")
    print(f"Compound balance:{state.compound.deposited_usdc:.6f} USDC")
    print(f"Wallet USDC:     {state.wallet.usdc_balance:.6f}")
    print(f"Wallet ETH:      {state.wallet.eth_balance:.6f}")
    print(f"Total capital:   {state.computed.total_capital_usdc:.6f} USDC")
    print()
    print(f"Gas price:  {state.network.gas_price_gwei:.6f} gwei")
    print(f"Gas cost:   ${state.network.gas_cost_estimate_usd:.6f}")
    print(f"Block:      {state.network.block_number}")
    print(f"Considerar mover? {state.computed.should_consider_move}")
