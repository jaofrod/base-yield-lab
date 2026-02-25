"""
main.py — Loop principal do bot. Orquestra todos os modulos.

Fluxo por ciclo (a cada 5 minutos):
1. LISTENER le dados on-chain → BotState
2. ENGINE consulta Claude → LLMAction
3. Se hold/alert: logar e pular
4. Se move_funds: FIREWALL valida → FirewallResult
5. Se firewall passou: EXECUTOR executa → resultado
6. Atualizar historico
7. Dormir POLL_INTERVAL_SECONDS

CONCEITO: Resiliencia
O bot roda 24/7. Qualquer excecao num ciclo (rede caiu, API timeout,
contrato reverteu) NAO pode derrubar o processo. O try/except no loop
garante que o bot continua tentando no proximo ciclo.

Um erro consecutivo aciona cooldown (COOLDOWN_AFTER_ERROR) para evitar
spam de requests quando algo esta sistematicamente errado.
"""

import logging
import sys
import time

from config import (
    POLL_INTERVAL_SECONDS,
    COOLDOWN_AFTER_ERROR,
    PAPER_TRADING,
    PUBLIC_ADDRESS,
    BASE_RPC_URL,
)
from state import (
    LLMAction,
    load_history,
    record_move,
    record_error,
    clear_errors,
)
from listener import build_state
from engine import get_decision
from firewall import validate_action
from executor import execute_action

# ============================================================
# LOGGING
#
# CONCEITO: Logging vs Print
# print() vai pro stdout e desaparece quando o terminal fecha.
# logging vai pro stdout E pro arquivo bot.log, com timestamp,
# nivel (INFO/WARNING/ERROR) e modulo de origem. Essencial
# para debugar problemas que aconteceram as 3h da manha.
# ============================================================

logger = logging.getLogger("bot")


def setup_logging():
    """Configura logging para console + arquivo."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # Arquivo
    file_handler = logging.FileHandler("bot.log")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


# ============================================================
# CICLO PRINCIPAL
# ============================================================


def run_cycle() -> None:
    """Executa um ciclo completo do bot.

    Pode ser chamado isoladamente para testes.
    """
    # 1. Ler estado on-chain
    logger.info("=" * 60)
    logger.info("INICIO DO CICLO")
    logger.info("=" * 60)

    state = build_state()

    logger.info(
        f"Aave: {state.aave.current_apy_pct:.4f}% APY, "
        f"{state.aave.deposited_usdc:.2f} USDC | "
        f"Compound: {state.compound.current_apy_pct:.4f}% APY, "
        f"{state.compound.deposited_usdc:.2f} USDC"
    )
    logger.info(
        f"Wallet: {state.wallet.usdc_balance:.2f} USDC, "
        f"{state.wallet.eth_balance:.6f} ETH | "
        f"Gas: {state.network.gas_price_gwei:.4f} gwei "
        f"(${state.network.gas_cost_estimate_usd:.4f})"
    )

    # 2. Consultar Claude
    action = get_decision(state)

    # 3. Se hold ou alert: logar e fim do ciclo
    if action.action == "hold":
        logger.info(f"DECISAO: HOLD — {action.reason}")
        return

    if action.action == "alert":
        logger.warning(f"ALERTA [{action.severity}]: {action.message}")
        return

    # 4. Se move_funds: validar com firewall
    logger.info(
        f"DECISAO: MOVE — {action.from_protocol} -> {action.to_protocol} "
        f"| {action.amount_usdc} USDC | {action.reason}"
    )

    # Resolver amount -1 (mover tudo) antes do firewall
    if action.amount_usdc == -1:
        if action.from_protocol == "aave_v3":
            action.amount_usdc = state.aave.deposited_usdc
        elif action.from_protocol == "compound_iii":
            action.amount_usdc = state.compound.deposited_usdc
        elif action.from_protocol == "wallet":
            action.amount_usdc = state.wallet.usdc_balance
        logger.info(f"Amount resolvido: {action.amount_usdc:.2f} USDC")

    firewall_result = validate_action(action, state)

    if not firewall_result.passed:
        logger.warning(f"FIREWALL BLOQUEOU: {firewall_result.failed_reasons}")
        return

    # 5. Executar
    result = execute_action(action)

    if result["status"] in ("success", "paper"):
        logger.info(f"EXECUCAO: {result['status'].upper()}")
        # Atualizar historico
        gas_cost = state.network.gas_cost_estimate_usd
        history = load_history()
        record_move(history, f"{action.from_protocol}->{action.to_protocol}", gas_cost)
    else:
        logger.error(f"EXECUCAO FALHOU: {result}")
        history = load_history()
        record_error(history)

    logger.info("FIM DO CICLO")


# ============================================================
# LOOP PRINCIPAL
# ============================================================


def main():
    """Loop infinito que roda run_cycle() a cada POLL_INTERVAL_SECONDS."""
    setup_logging()

    mode = "PAPER TRADING" if PAPER_TRADING else "LIVE TRADING"
    logger.info(f"Bot iniciando em modo: {mode}")
    logger.info(f"Wallet: {PUBLIC_ADDRESS}")
    logger.info(f"RPC: {BASE_RPC_URL[:50]}...")
    logger.info(f"Intervalo de polling: {POLL_INTERVAL_SECONDS}s")
    logger.info("")

    history = load_history()
    if history.consecutive_errors > 0:
        logger.warning(f"Historico carregado: {history.consecutive_errors} erros consecutivos")
    clear_errors(history)

    while True:
        try:
            run_cycle()
        except KeyboardInterrupt:
            logger.info("Bot parado pelo usuario (Ctrl+C)")
            break
        except Exception as e:
            logger.error(f"ERRO NO CICLO: {e}", exc_info=True)
            history = load_history()
            history = record_error(history)

            if history.consecutive_errors >= 3:
                logger.error(
                    f"3+ erros consecutivos. Cooldown de {COOLDOWN_AFTER_ERROR}s"
                )
                time.sleep(COOLDOWN_AFTER_ERROR)
            else:
                # Espera curta antes de tentar de novo
                time.sleep(30)
            continue

        logger.info(f"Proximo ciclo em {POLL_INTERVAL_SECONDS}s...")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
