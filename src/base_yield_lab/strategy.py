"""
strategy.py — Deterministic action selection.

This module is the hot path for deciding whether the bot should hold or
propose a fund movement. It performs no network or AI calls.
"""

from config import MIN_APY_ABSOLUTE, MIN_APY_DIFF
from state import BotAction, BotState


def choose_action(state: BotState) -> BotAction:
    """Return the deterministic action for the current state."""
    computed = state.computed

    if computed.total_capital_usdc <= 0:
        return BotAction(action="hold", reason="No USDC capital available.")

    if state.wallet.usdc_balance > 0 and computed.best_apy_pct >= MIN_APY_ABSOLUTE:
        return BotAction(
            action="move_funds",
            from_protocol="wallet",
            to_protocol=computed.best_protocol,
            amount_usdc=state.wallet.usdc_balance,
            reason=(
                "Idle wallet USDC is available and the best protocol meets "
                "the minimum APY threshold."
            ),
        )

    if computed.current_protocol == "none":
        return BotAction(action="hold", reason="No active protocol position.")

    if computed.apy_diff_pct < MIN_APY_DIFF:
        return BotAction(
            action="hold",
            reason=(
                f"APY spread {computed.apy_diff_pct:.4f}% is below the "
                f"{MIN_APY_DIFF:.4f}% movement threshold."
            ),
        )

    if computed.best_protocol == computed.current_protocol:
        return BotAction(
            action="hold",
            reason="Current position is already in the best-yielding protocol.",
        )

    if computed.best_apy_pct < MIN_APY_ABSOLUTE:
        return BotAction(
            action="hold",
            reason=(
                f"Best APY {computed.best_apy_pct:.4f}% is below the "
                f"{MIN_APY_ABSOLUTE:.4f}% minimum."
            ),
        )

    amount = 0.0
    if computed.current_protocol == "aave_v3":
        amount = state.aave.deposited_usdc
    elif computed.current_protocol == "compound_iii":
        amount = state.compound.deposited_usdc

    if amount <= 0:
        return BotAction(action="hold", reason="Current protocol has no USDC balance.")

    return BotAction(
        action="move_funds",
        from_protocol=computed.current_protocol,
        to_protocol=computed.best_protocol,
        amount_usdc=amount,
        reason=(
            f"{computed.best_protocol} APY exceeds current protocol by "
            f"{computed.apy_diff_pct:.4f}%."
        ),
    )
