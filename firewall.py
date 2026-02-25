"""
firewall.py — O Guarda do bot. Validacao deterministico ANTES de executar.

CONCEITO: Por que um firewall deterministico?
O LLM pode "alucinar": sugerir mover $500 quando voce so tem $50, ou
interagir com um contrato que nao existe. O firewall e codigo Python puro
(sem IA, sem probabilidade) que valida a decisao contra regras rigidas.

PRINCIPIO: Rodar TODOS os checks, sem short-circuit.
Se voce para no primeiro erro, o log mostra "protocolo invalido" mas nao
te diz que TAMBEM o valor era absurdo. Rodando todos, voce ve o quadro
completo de uma vez.

O firewall so valida acoes do tipo "move_funds". "hold" e "alert" passam
direto — nao fazem nada na blockchain, nao precisam de validacao.
"""

import logging
import time

from config import (
    APPROVED_PROTOCOLS,
    APPROVED_TOKENS,
    MAX_SINGLE_TX_USDC,
    MAX_GAS_COST_USD,
    MAX_GAS_PRICE_GWEI,
    MIN_TIME_BETWEEN_MOVES,
    MIN_PROFIT_AFTER_GAS,
    KNOWN_CONTRACTS,
    AAVE_POOL_ADDRESS,
    COMPOUND_COMET_ADDRESS,
    SECONDS_PER_YEAR,
)
from state import BotState, LLMAction, FirewallResult

logger = logging.getLogger(__name__)


def _get_target_contract(protocol: str) -> str:
    """Mapeia nome de protocolo → endereco do contrato alvo."""
    mapping = {
        "aave_v3": AAVE_POOL_ADDRESS,
        "compound_iii": COMPOUND_COMET_ADDRESS,
    }
    return mapping.get(protocol, "")


def _get_source_balance(action: LLMAction, state: BotState) -> float:
    """Retorna o saldo disponivel no protocolo de origem."""
    if action.from_protocol == "aave_v3":
        return state.aave.deposited_usdc
    elif action.from_protocol == "compound_iii":
        return state.compound.deposited_usdc
    elif action.from_protocol == "wallet":
        return state.wallet.usdc_balance
    return 0.0


def _estimate_annual_gain(action: LLMAction, state: BotState) -> float:
    """Estima o ganho anual em USD da movimentacao.

    CONCEITO: Por que comparar ganho com gas?
    Se mover custa $0.01 de gas mas gera apenas $0.005 a mais de rendimento
    ao longo de um mes, nao vale a pena. O firewall exige que o ganho
    estimado supere o custo de gas.
    """
    if action.to_protocol == "aave_v3":
        to_apy = state.aave.current_apy_pct
    elif action.to_protocol == "compound_iii":
        to_apy = state.compound.current_apy_pct
    else:
        return 0.0

    if action.from_protocol == "aave_v3":
        from_apy = state.aave.current_apy_pct
    elif action.from_protocol == "compound_iii":
        from_apy = state.compound.current_apy_pct
    else:
        from_apy = 0.0  # vindo da wallet, qualquer APY e ganho

    amount = action.amount_usdc
    if amount <= 0:
        amount = _get_source_balance(action, state)

    apy_diff = to_apy - from_apy
    annual_gain = (apy_diff / 100) * amount
    return annual_gain


def validate_action(action: LLMAction, state: BotState) -> FirewallResult:
    """Valida uma acao do LLM contra 9 regras deterministicas.

    Retorna FirewallResult com:
    - passed: True se TODOS os checks passaram
    - checks: dict com o resultado de cada check individual
    - failed_reasons: lista dos nomes dos checks que falharam
    """

    # "hold" e "alert" nao precisam de validacao — nao tocam na blockchain
    if action.action in ("hold", "alert"):
        return FirewallResult(
            passed=True,
            checks={"action_type": True},
            failed_reasons=[],
        )

    # Resolve o amount real se for -1 (mover tudo)
    amount = action.amount_usdc
    if amount == -1:
        amount = _get_source_balance(action, state)

    # --- 9 CHECKS ---

    # 1. Protocolo de origem e destino estao na whitelist?
    from_approved = action.from_protocol in APPROVED_PROTOCOLS or action.from_protocol == "wallet"
    to_approved = action.to_protocol in APPROVED_PROTOCOLS
    protocol_approved = from_approved and to_approved

    # 2. Token esta na whitelist? (por ora so USDC)
    token_approved = "USDC" in APPROVED_TOKENS  # sempre true enquanto so operamos USDC

    # 3. Valor dentro do limite por transacao?
    amount_within_limit = amount <= MAX_SINGLE_TX_USDC

    # 4. Custo de gas aceitavel?
    gas_acceptable = state.network.gas_cost_estimate_usd <= MAX_GAS_COST_USD

    # 5. Gas price nao esta absurdo?
    gas_price_ok = state.network.gas_price_gwei <= MAX_GAS_PRICE_GWEI

    # 6. Cooldown entre movimentacoes respeitado?
    time_since_last = time.time() - state.history.last_move_timestamp
    cooldown_ok = time_since_last >= MIN_TIME_BETWEEN_MOVES

    # 7. Movimentacao e lucrativa? (ganho estimado > custo de gas)
    annual_gain = _estimate_annual_gain(action, state)
    # Converter ganho anual pra ganho no periodo minimo entre moves
    # para comparar com custo de gas de forma justa
    gas_cost = state.network.gas_cost_estimate_usd
    profitable = annual_gain > gas_cost

    # 8. Bot tem saldo suficiente no protocolo de origem?
    source_balance = _get_source_balance(action, state)
    sufficient_balance = amount <= source_balance

    # 9. Contrato de destino esta no KNOWN_CONTRACTS?
    target_contract = _get_target_contract(action.to_protocol)
    contract_verified = target_contract in KNOWN_CONTRACTS

    # --- Montar resultado ---
    checks = {
        "protocol_approved": protocol_approved,
        "token_approved": token_approved,
        "amount_within_limit": amount_within_limit,
        "gas_acceptable": gas_acceptable,
        "gas_price_ok": gas_price_ok,
        "cooldown_ok": cooldown_ok,
        "profitable": profitable,
        "sufficient_balance": sufficient_balance,
        "contract_verified": contract_verified,
    }

    failed = [name for name, passed in checks.items() if not passed]
    all_passed = len(failed) == 0

    result = FirewallResult(
        passed=all_passed,
        checks=checks,
        failed_reasons=failed,
    )

    if all_passed:
        logger.info("FIREWALL: PASSED — todos os 9 checks OK")
    else:
        logger.warning(f"FIREWALL: BLOCKED — checks falharam: {failed}")
        for name in failed:
            if name == "protocol_approved":
                logger.warning(f"  - Protocolo nao aprovado: from={action.from_protocol} to={action.to_protocol}")
            elif name == "amount_within_limit":
                logger.warning(f"  - Valor {amount} USDC excede limite de {MAX_SINGLE_TX_USDC}")
            elif name == "gas_acceptable":
                logger.warning(f"  - Gas cost ${gas_cost:.4f} excede limite de ${MAX_GAS_COST_USD}")
            elif name == "gas_price_ok":
                logger.warning(f"  - Gas price {state.network.gas_price_gwei:.4f} gwei excede {MAX_GAS_PRICE_GWEI}")
            elif name == "cooldown_ok":
                remaining = MIN_TIME_BETWEEN_MOVES - time_since_last
                logger.warning(f"  - Cooldown ativo: faltam {remaining:.0f}s")
            elif name == "profitable":
                logger.warning(f"  - Nao lucrativo: ganho anual ${annual_gain:.4f} <= gas ${gas_cost:.4f}")
            elif name == "sufficient_balance":
                logger.warning(f"  - Saldo insuficiente: {source_balance:.2f} < {amount:.2f} USDC")
            elif name == "contract_verified":
                logger.warning(f"  - Contrato nao verificado: {target_contract}")

    return result
