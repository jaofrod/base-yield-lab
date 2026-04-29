"""
analyst.py — Optional AI run analysis.

The analyst is a cold-path helper. It summarizes a completed deterministic
run but never chooses, changes, approves, or executes actions.
"""

import json
import logging
from dataclasses import asdict

import anthropic

from config import ANTHROPIC_API_KEY
from state import BotAction, BotState, FirewallResult

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """You summarize BaseRoute bot runs for a human operator.

Core constraints:
- Deterministic strategy code already chose the action.
- The deterministic firewall already passed or blocked the action.
- You must not choose actions, approve transactions, change amounts, or bypass checks.
- Explain what happened, why it likely happened, and any unusual conditions.

Keep the summary concise and educational."""


def _run_payload(
    state: BotState,
    action: BotAction,
    firewall_result: FirewallResult | None = None,
    execution_result: dict | None = None,
) -> str:
    """Serialize the run into compact JSON for analysis."""
    payload = {
        "state": asdict(state),
        "deterministic_action": asdict(action),
        "firewall_result": asdict(firewall_result) if firewall_result else None,
        "execution_result": execution_result,
    }
    return json.dumps(payload, indent=2, default=str)


def analyze_run(
    state: BotState,
    action: BotAction,
    firewall_result: FirewallResult | None = None,
    execution_result: dict | None = None,
) -> str:
    """Return an optional AI explanation of a completed run."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    user_message = (
        "Analyze this completed run. Do not recommend bypassing strategy or "
        f"firewall rules.\n\n{_run_payload(state, action, firewall_result, execution_result)}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=700,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text_parts = [
        block.text for block in response.content if getattr(block, "type", "") == "text"
    ]
    summary = "\n".join(text_parts).strip()
    logger.info("AI run analysis completed.")
    return summary
