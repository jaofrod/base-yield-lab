"""
state.py — Estruturas de dados e persistencia do bot.

CONCEITO: Por que dataclasses em vez de dicts?
Com dicts, um typo como state["apy_dif"] (faltou o 'f') retorna None
silenciosamente. Com dataclasses, Python levanta AttributeError na hora.
Erros ruidosos sao BONS — voce pega bugs cedo.

Dataclasses sao uma forma elegante do Python de criar "structs" —
containers de dados com campos tipados, sem precisar escrever __init__
manualmente.
"""

import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Optional


# ============================================================
# DATACLASSES DE ESTADO
# Cada uma representa uma "fatia" do estado do mundo que o bot
# precisa conhecer num dado momento.
# ============================================================

@dataclass
class NetworkState:
    """Estado da rede Base neste instante."""
    chain_id: int = 0
    gas_price_gwei: float = 0.0
    gas_cost_estimate_usd: float = 0.0
    block_number: int = 0


@dataclass
class WalletState:
    """Saldos da wallet do bot."""
    address: str = ""
    usdc_balance: float = 0.0  # USDC livre (nao depositado em nenhum protocolo)
    eth_balance: float = 0.0   # ETH para pagar gas


@dataclass
class ProtocolPosition:
    """Posicao do bot num protocolo especifico."""
    deposited_usdc: float = 0.0
    current_apy_pct: float = 0.0


@dataclass
class ComputedState:
    """Valores calculados a partir dos dados brutos.

    CONCEITO: Separar dados brutos de computados
    O listener le dados crus da blockchain. Aqui a gente deriva
    informacoes uteis (qual protocolo e melhor, qual a diferenca
    de APY, etc). Isso evita que o LLM precise fazer contas.
    """
    total_capital_usdc: float = 0.0
    best_protocol: str = ""
    best_apy_pct: float = 0.0
    current_protocol: str = ""  # onde esta o capital agora
    current_apy_pct: float = 0.0
    apy_diff_pct: float = 0.0
    should_consider_move: bool = False
    estimated_annual_gain_if_move: float = 0.0
    estimated_gas_cost_for_move: float = 0.0


@dataclass
class HistoryState:
    """Historico recente de acoes do bot.

    CONCEITO: Cooldown
    Sem cooldown, o bot pode entrar num loop: "Aave melhor -> move ->
    Compound melhor -> move -> Aave melhor -> move..." gastando gas
    sem parar. O cooldown forca um intervalo minimo entre movimentacoes.
    """
    last_move_timestamp: float = 0.0  # Unix timestamp
    last_move_action: str = ""
    total_moves_24h: int = 0
    total_gas_spent_24h_usd: float = 0.0
    consecutive_errors: int = 0


@dataclass
class BotState:
    """Estado completo do bot num instante. Agrupa tudo."""
    timestamp: float = 0.0
    network: NetworkState = field(default_factory=NetworkState)
    wallet: WalletState = field(default_factory=WalletState)
    aave: ProtocolPosition = field(default_factory=ProtocolPosition)
    compound: ProtocolPosition = field(default_factory=ProtocolPosition)
    computed: ComputedState = field(default_factory=ComputedState)
    history: HistoryState = field(default_factory=HistoryState)


# ============================================================
# DATACLASS DE ACAO DO LLM
# ============================================================

@dataclass
class LLMAction:
    """Decisao do LLM apos analisar o estado.

    action pode ser: "hold", "move_funds", "alert"
    """
    action: str = "hold"  # hold | move_funds | alert
    from_protocol: str = ""  # aave_v3 | compound_iii | wallet
    to_protocol: str = ""  # aave_v3 | compound_iii
    amount_usdc: float = 0.0  # quanto mover (-1 = tudo)
    reason: str = ""
    # Campos para alert
    severity: str = ""  # info | warning | critical
    message: str = ""


# ============================================================
# DATACLASS DO FIREWALL
# ============================================================

@dataclass
class FirewallResult:
    """Resultado da validacao do firewall.

    Todos os 9 checks rodam SEMPRE (sem short-circuit), assim
    o log mostra TUDO que falhou, nao so o primeiro problema.
    """
    passed: bool = True
    checks: dict = field(default_factory=dict)
    failed_reasons: list = field(default_factory=list)


# ============================================================
# PERSISTENCIA — bot_history.json
#
# CONCEITO: Por que persistir em arquivo?
# Se o bot reiniciar (crash, deploy, reboot), sem persistencia
# ele "esquece" que moveu fundos ha 5 minutos e pode mover de
# novo imediatamente. O arquivo JSON garante que o cooldown
# sobrevive restarts.
# ============================================================

HISTORY_FILE = "bot_history.json"


def load_history() -> HistoryState:
    """Carrega historico do disco. Retorna vazio se nao existir."""
    if not os.path.exists(HISTORY_FILE):
        return HistoryState()
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
        return HistoryState(
            last_move_timestamp=data.get("last_move_timestamp", 0.0),
            last_move_action=data.get("last_move_action", ""),
            total_moves_24h=data.get("total_moves_24h", 0),
            total_gas_spent_24h_usd=data.get("total_gas_spent_24h_usd", 0.0),
            consecutive_errors=data.get("consecutive_errors", 0),
        )
    except (json.JSONDecodeError, KeyError):
        return HistoryState()


def save_history(history: HistoryState) -> None:
    """Salva historico no disco."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(asdict(history), f, indent=2)


def record_move(history: HistoryState, action: str, gas_cost_usd: float) -> HistoryState:
    """Registra uma movimentacao bem-sucedida."""
    now = time.time()

    # Reseta contador de 24h se ja passou 1 dia
    if now - history.last_move_timestamp > 86400:
        moves_24h = 1
        gas_24h = gas_cost_usd
    else:
        moves_24h = history.total_moves_24h + 1
        gas_24h = history.total_gas_spent_24h_usd + gas_cost_usd

    updated = HistoryState(
        last_move_timestamp=now,
        last_move_action=action,
        total_moves_24h=moves_24h,
        total_gas_spent_24h_usd=gas_24h,
        consecutive_errors=0,  # reset apos sucesso
    )
    save_history(updated)
    return updated


def record_error(history: HistoryState) -> HistoryState:
    """Registra um erro consecutivo."""
    updated = HistoryState(
        last_move_timestamp=history.last_move_timestamp,
        last_move_action=history.last_move_action,
        total_moves_24h=history.total_moves_24h,
        total_gas_spent_24h_usd=history.total_gas_spent_24h_usd,
        consecutive_errors=history.consecutive_errors + 1,
    )
    save_history(updated)
    return updated


def clear_errors(history: HistoryState) -> HistoryState:
    """Limpa contador de erros consecutivos."""
    updated = HistoryState(
        last_move_timestamp=history.last_move_timestamp,
        last_move_action=history.last_move_action,
        total_moves_24h=history.total_moves_24h,
        total_gas_spent_24h_usd=history.total_gas_spent_24h_usd,
        consecutive_errors=0,
    )
    save_history(updated)
    return updated
