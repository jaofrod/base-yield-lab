"""
config.py — Configuracao centralizada do bot.

Tudo que os outros modulos precisam saber (enderecos, ABIs, thresholds)
vive aqui. Zero logica, so constantes e leitura de .env.

CONCEITO: Por que centralizar config?
Quando voce tem enderecos de contratos espalhados em 5 arquivos diferentes,
um typo num unico caractere hex pode fazer voce interagir com o contrato
ERRADO — e perder fundos. Centralizar garante uma unica fonte de verdade.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# SECRETS (do .env)
# ============================================================
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
PUBLIC_ADDRESS = os.getenv("PUBLIC_ADDRESS", "")
BASE_RPC_URL = os.getenv("BASE_RPC_URL", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
PAPER_TRADING = os.getenv("PAPER_TRADING", "true").lower() == "true"

# ============================================================
# REDE: Base (L2 do Ethereum)
# ============================================================
CHAIN_ID = 8453

# ============================================================
# ENDERECOS DE CONTRATOS NA BASE
#
# CONCEITO: Checksum address
# Enderecos Ethereum sao hex de 40 caracteres. O "checksum" (EIP-55)
# mistura maiusculas/minusculas para detectar typos. Se voce errar
# um caractere, o checksum falha e web3.py rejeita o endereco.
# Sempre use enderecos com checksum.
# ============================================================

# USDC nativo na Base (emitido pela Circle, 6 decimais)
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# Aave V3 na Base
AAVE_POOL_ADDRESS = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"
AAVE_DATA_PROVIDER_ADDRESS = "0x0F43731EB8d45A581f4a36DD74F5f358bc90C73A"
AAVE_AUSDC_ADDRESS = "0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB"

# Compound III (Comet) na Base — mercado USDC
COMPOUND_COMET_ADDRESS = "0xb125E6687d4313864e53df431d5425969c15Eb2F"

# ============================================================
# KNOWN_CONTRACTS — whitelist para o firewall
#
# Qualquer contrato com quem o bot interage PRECISA estar aqui.
# Se o LLM "alucinar" e sugerir interagir com um contrato
# desconhecido, o firewall bloqueia.
# ============================================================
KNOWN_CONTRACTS = {
    USDC_ADDRESS,
    AAVE_POOL_ADDRESS,
    AAVE_DATA_PROVIDER_ADDRESS,
    AAVE_AUSDC_ADDRESS,
    COMPOUND_COMET_ADDRESS,
}

# ============================================================
# ABIs (Application Binary Interface)
#
# CONCEITO: ABI
# Contratos na blockchain sao bytecode compilado — binario puro.
# A ABI é o "manual de instrucoes" que diz quais funcoes existem,
# quais parametros aceitam, e o que retornam. Sem ABI, voce nao
# consegue chamar funcoes do contrato de forma tipada.
#
# Aqui usamos ABIs parciais — so as funcoes que o bot precisa.
# Nao precisamos da ABI completa (que pode ter centenas de funcoes).
# ============================================================

USDC_ABI = [
    {
        "name": "balanceOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "approve",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
    },
    {
        "name": "allowance",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
        ],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "decimals",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint8"}],
    },
]

AAVE_POOL_ABI = [
    {
        "name": "supply",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "asset", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "onBehalfOf", "type": "address"},
            {"name": "referralCode", "type": "uint16"},
        ],
        "outputs": [],
    },
    {
        "name": "withdraw",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "asset", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "to", "type": "address"},
        ],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "getReserveData",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "asset", "type": "address"}],
        "outputs": [
            {
                "name": "",
                "type": "tuple",
                "components": [
                    {"name": "configuration", "type": "uint256"},
                    {"name": "liquidityIndex", "type": "uint128"},
                    {"name": "currentLiquidityRate", "type": "uint128"},
                    {"name": "variableBorrowIndex", "type": "uint128"},
                    {"name": "currentVariableBorrowRate", "type": "uint128"},
                    {"name": "currentStableBorrowRate", "type": "uint128"},
                    {"name": "lastUpdateTimestamp", "type": "uint40"},
                    {"name": "id", "type": "uint16"},
                    {"name": "aTokenAddress", "type": "address"},
                    {"name": "stableDebtTokenAddress", "type": "address"},
                    {"name": "variableDebtTokenAddress", "type": "address"},
                    {"name": "interestRateStrategyAddress", "type": "address"},
                    {"name": "accruedToTreasury", "type": "uint128"},
                    {"name": "unbacked", "type": "uint128"},
                    {"name": "isolationModeTotalDebt", "type": "uint128"},
                ],
            }
        ],
    },
]

AAVE_DATA_PROVIDER_ABI = [
    {
        "name": "getUserReserveData",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "asset", "type": "address"},
            {"name": "user", "type": "address"},
        ],
        "outputs": [
            {"name": "currentATokenBalance", "type": "uint256"},
            {"name": "currentStableDebt", "type": "uint256"},
            {"name": "currentVariableDebt", "type": "uint256"},
            {"name": "principalStableDebt", "type": "uint256"},
            {"name": "scaledVariableDebt", "type": "uint256"},
            {"name": "stableBorrowRate", "type": "uint256"},
            {"name": "liquidityRate", "type": "uint256"},
            {"name": "stableRateLastUpdated", "type": "uint40"},
            {"name": "usageAsCollateralEnabled", "type": "bool"},
        ],
    }
]

COMPOUND_COMET_ABI = [
    {
        "name": "supply",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "asset", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [],
    },
    {
        "name": "withdraw",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "asset", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [],
    },
    {
        "name": "balanceOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "getUtilization",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "getSupplyRate",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "utilization", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint64"}],
    },
    {
        "name": "totalSupply",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
]

# ============================================================
# THRESHOLDS DE DECISAO
# ============================================================

# Capital
INITIAL_CAPITAL_USDC = 50
MIN_POSITION_SIZE = 5  # minimo em USDC para valer a pena mover

# APY
MIN_APY_DIFF = 1.5  # diferenca minima de APY (%) para considerar mover
MIN_APY_ABSOLUTE = 0.5  # APY minimo absoluto do destino (%)

# Gas / Custo
MAX_GAS_COST_USD = 0.10  # maximo aceitavel por operacao (USD)
MIN_PROFIT_AFTER_GAS = 0.01  # lucro minimo liquido apos gas (USD)

# Seguranca
MAX_SINGLE_TX_USDC = 50  # maximo por transacao
APPROVED_PROTOCOLS = ["aave_v3", "compound_iii"]
APPROVED_TOKENS = ["USDC"]
MAX_GAS_PRICE_GWEI = 0.5  # gas price maximo aceitavel na Base

# Timing
POLL_INTERVAL_SECONDS = 300  # checar taxas a cada 5 minutos
MIN_TIME_BETWEEN_MOVES = 3600  # minimo 1 hora entre movimentacoes
COOLDOWN_AFTER_ERROR = 600  # 10 min de espera apos erro

# ============================================================
# CONSTANTES MATEMATICAS
#
# CONCEITO: Por que esses numeros malucos?
# Blockchains nao suportam numeros decimais (float). Tudo e inteiro.
# Entao cada protocolo inventa uma "escala" para representar decimais:
# - USDC usa 6 decimais: 1 USDC = 1_000_000 unidades on-chain
# - Aave usa "ray" (27 decimais): 1.0 = 10^27
# - Compound usa 18 decimais: 1.0 = 10^18
# ============================================================
RAY = 10**27  # Escala do Aave para taxas
SECONDS_PER_YEAR = 31_536_000  # 365 * 24 * 60 * 60
USDC_DECIMALS = 6

# Gas fixo para transacoes DeFi (conservador, sobra e refundada)
DEFAULT_GAS_LIMIT = 300_000

# Preco estimado de ETH em USD (para calcular custo de gas em USD)
# Em producao, isso viria de um oracle ou API. Por ora, constante.
ETH_PRICE_USD = 2500.0
