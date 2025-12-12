import unittest
from unittest.mock import MagicMock, patch

from src.agents.rl_agent import RLFilter
from src.orchestrator.main import TradingOrchestrator


class TestHeuristicOptimization(unittest.TestCase):
    def setUp(self):
        self.rl_filter = RLFilter()

    def test_rl_filter_vix_adjustment(self):
        """Test that VIX levels affect the confidence score."""
        # Baseline (VIX=20)
        base_state = {"strength": 0.8, "momentum": 0.5, "vix_level": 20.0}
        base_pred = self.rl_filter._predict_with_heuristics("TEST", base_state)

        # High VIX (Crisis) -> Should have lower confidence (z -= 0.5)
        crisis_state = base_state.copy()
        crisis_state["vix_level"] = 40.0
        crisis_pred = self.rl_filter._predict_with_heuristics("TEST", crisis_state)

        # Low VIX (Bull) -> Should have higher confidence (z += 0.2)
        bull_state = base_state.copy()
        bull_state["vix_level"] = 12.0
        bull_pred = self.rl_filter._predict_with_heuristics("TEST", bull_state)

        print(f"Base Confidence: {base_pred['confidence']}")
        print(f"Crisis Confidence: {crisis_pred['confidence']}")
        print(f"Bull Confidence: {bull_pred['confidence']}")

        self.assertLess(
            crisis_pred["confidence"], base_pred["confidence"], "Crisis VIX should lower confidence"
        )
        self.assertGreater(
            bull_pred["confidence"], base_pred["confidence"], "Low VIX should boost confidence"
        )

    @patch("src.orchestrator.main.RegimeDetector")
    @patch("src.orchestrator.main.AlpacaExecutor")
    @patch("src.orchestrator.main.RiskManager")
    def test_orchestrator_vix_injection(self, mock_risk, mock_executor, mock_regime_cls):
        """Test that Orchestrator injects VIX into momentum signal."""
        # Setup mocks
        mock_regime_instance = mock_regime_cls.return_value
        mock_snapshot = MagicMock()
        mock_snapshot.vix_level = 35.0
        mock_snapshot.label = "spike"
        mock_regime_instance.detect_live_regime.return_value = mock_snapshot

        # Init Orchestrator
        orch = TradingOrchestrator(tickers=["SPY"], paper=True)

        # Mock dependencies to avoid side effects
        orch.momentum_agent = MagicMock()
        mock_signal = MagicMock()
        mock_signal.is_buy = True
        mock_signal.strength = 0.8
        mock_signal.indicators = {"some_ind": 1.0}

        # Make failure manager return our mock signal for MOMENTUM, then RL decision
        momentum_outcome = MagicMock()
        momentum_outcome.ok = True
        momentum_outcome.result = mock_signal

        rl_outcome = MagicMock()
        rl_outcome.ok = True
        rl_outcome.result = {"confidence": 0.9, "action": "BUY"}

        orch.failure_manager = MagicMock()
        orch.failure_manager.run.side_effect = [momentum_outcome, rl_outcome]

        # Mock RL filter
        orch.rl_filter = MagicMock()
        orch.rl_filter_enabled = True
        orch.rl_filter.predict.return_value = {"confidence": 0.9, "action": "BUY"}

        # Run process_ticker (partial mock via _build_session_profile injection)
        # We need to manually set the session profile since we aren't calling run()
        orch.session_profile = {
            "tickers": ["SPY"],
            "regime_snapshot": mock_snapshot,
            "rl_threshold": 0.5,
        }

        # Call process_ticker
        orch._process_ticker("SPY", 0.5)

        # Check if indicators were updated
        self.assertIn("vix_level", mock_signal.indicators)
        self.assertEqual(mock_signal.indicators["vix_level"], 35.0)
        self.assertEqual(mock_signal.indicators["market_regime"], "spike")


if __name__ == "__main__":
    unittest.main()
