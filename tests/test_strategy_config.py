import sys
import types
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src" / "base_yield_lab"
sys.path.insert(0, str(SRC_DIR))

import config
import main
from state import BotState, ComputedState, ProtocolPosition, WalletState
from strategy import choose_action


def make_state(
    *,
    wallet_usdc=0.0,
    aave_balance=0.0,
    compound_balance=0.0,
    aave_apy=1.0,
    compound_apy=1.0,
    current_protocol="none",
    best_protocol="aave_v3",
):
    best_apy = aave_apy if best_protocol == "aave_v3" else compound_apy
    current_apy = 0.0
    if current_protocol == "aave_v3":
        current_apy = aave_apy
    elif current_protocol == "compound_iii":
        current_apy = compound_apy

    return BotState(
        wallet=WalletState(usdc_balance=wallet_usdc),
        aave=ProtocolPosition(aave_balance, aave_apy),
        compound=ProtocolPosition(compound_balance, compound_apy),
        computed=ComputedState(
            total_capital_usdc=wallet_usdc + aave_balance + compound_balance,
            best_protocol=best_protocol,
            best_apy_pct=best_apy,
            current_protocol=current_protocol,
            current_apy_pct=current_apy,
            apy_diff_pct=abs(aave_apy - compound_apy),
        ),
    )


class StrategyTests(unittest.TestCase):
    def test_holds_when_apy_difference_is_below_threshold(self):
        state = make_state(
            aave_balance=10,
            aave_apy=2.0,
            compound_apy=2.5,
            current_protocol="aave_v3",
            best_protocol="compound_iii",
        )

        action = choose_action(state)

        self.assertEqual(action.action, "hold")

    def test_moves_wallet_usdc_to_best_protocol(self):
        state = make_state(
            wallet_usdc=10,
            aave_apy=3.0,
            compound_apy=1.0,
            best_protocol="aave_v3",
        )

        action = choose_action(state)

        self.assertEqual(action.action, "move_funds")
        self.assertEqual(action.from_protocol, "wallet")
        self.assertEqual(action.to_protocol, "aave_v3")
        self.assertEqual(action.amount_usdc, 10)

    def test_moves_from_worse_protocol_to_better_protocol(self):
        state = make_state(
            compound_balance=20,
            aave_apy=4.0,
            compound_apy=1.0,
            current_protocol="compound_iii",
            best_protocol="aave_v3",
        )

        action = choose_action(state)

        self.assertEqual(action.action, "move_funds")
        self.assertEqual(action.from_protocol, "compound_iii")
        self.assertEqual(action.to_protocol, "aave_v3")
        self.assertEqual(action.amount_usdc, 20)

    def test_holds_when_already_in_best_protocol(self):
        state = make_state(
            aave_balance=20,
            aave_apy=4.0,
            compound_apy=1.0,
            current_protocol="aave_v3",
            best_protocol="aave_v3",
        )

        action = choose_action(state)

        self.assertEqual(action.action, "hold")


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.original = {
            "PRIVATE_KEY": config.PRIVATE_KEY,
            "PUBLIC_ADDRESS": config.PUBLIC_ADDRESS,
            "BASE_RPC_URL": config.BASE_RPC_URL,
            "ANTHROPIC_API_KEY": config.ANTHROPIC_API_KEY,
        }

    def tearDown(self):
        for name, value in self.original.items():
            setattr(config, name, value)

    def test_validation_does_not_require_ai_by_default(self):
        config.PRIVATE_KEY = "key"
        config.PUBLIC_ADDRESS = "0x123"
        config.BASE_RPC_URL = "https://example.invalid"
        config.ANTHROPIC_API_KEY = ""

        self.assertEqual(config.validate_runtime_config(), [])

    def test_validation_requires_ai_when_requested(self):
        config.PRIVATE_KEY = "key"
        config.PUBLIC_ADDRESS = "0x123"
        config.BASE_RPC_URL = "https://example.invalid"
        config.ANTHROPIC_API_KEY = ""

        self.assertEqual(config.validate_runtime_config(require_ai=True), ["ANTHROPIC_API_KEY"])


class AiAnalysisTests(unittest.TestCase):
    def test_ai_analysis_failure_does_not_raise(self):
        fake_analyst = types.ModuleType("analyst")

        def fail(*args, **kwargs):
            raise RuntimeError("analysis unavailable")

        fake_analyst.analyze_run = fail
        original = sys.modules.get("analyst")
        sys.modules["analyst"] = fake_analyst
        try:
            with self.assertLogs("bot", level="WARNING"):
                main._run_ai_analysis(BotState(), choose_action(BotState()))
        finally:
            if original is None:
                del sys.modules["analyst"]
            else:
                sys.modules["analyst"] = original


if __name__ == "__main__":
    unittest.main()
