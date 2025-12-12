import sys
import unittest
from datetime import date
from unittest.mock import patch

# Add src to path
sys.path.append(".")

# We need to patch the imports BEFORE importing OptionsExecutor
# or patch them where they are used.
# Since we import OptionsExecutor at module level, we should preserve that
# but rely on patch context managers in setUp.

from src.trading.options_executor import OptionsExecutor


class TestOptionsExecutorFixes(unittest.TestCase):
    def setUp(self):
        # Patch the classes used in OptionsExecutor.__init__
        self.client_patcher = patch("src.trading.options_executor.AlpacaOptionsClient")
        self.trader_patcher = patch("src.trading.options_executor.AlpacaTrader")
        self.risk_patcher = patch("src.trading.options_executor.OptionsRiskMonitor")

        self.MockOptionsClient = self.client_patcher.start()
        self.MockTrader = self.trader_patcher.start()
        self.MockRiskMonitor = self.risk_patcher.start()

        self.executor = OptionsExecutor(paper=True)

        # Setup mock behavior
        self.executor.trader.get_account_info.return_value = {
            "equity": "100000",
            "buying_power": "100000",
        }

    def tearDown(self):
        self.client_patcher.stop()
        self.trader_patcher.stop()
        self.risk_patcher.stop()

    def test_parse_option_symbol_spy(self):
        symbol = "SPY251219C00600000"
        parsed = self.executor._parse_option_symbol(symbol)
        self.assertEqual(parsed["ticker"], "SPY")
        self.assertEqual(parsed["expiration"], date(2025, 12, 19))
        self.assertEqual(parsed["type"], "call")
        self.assertEqual(parsed["strike"], 600.0)

    def test_parse_option_symbol_aapl(self):
        # 4 letter ticker
        symbol = "AAPL251219P00250000"
        parsed = self.executor._parse_option_symbol(symbol)
        self.assertEqual(parsed["ticker"], "AAPL")
        self.assertEqual(parsed["expiration"], date(2025, 12, 19))
        self.assertEqual(parsed["type"], "put")
        self.assertEqual(parsed["strike"], 250.0)

    def test_client_order_id_passed(self):
        # Call place_paper_order
        self.executor.place_paper_order(
            "SPY251219C00600000", 1, "buy_to_open", 5.0, client_order_id="test_strategy_id"
        )

        # Verify the mock client's submit_option_order was called with client_order_id
        self.executor.options_client.submit_option_order.assert_called_with(
            option_symbol="SPY251219C00600000",
            qty=1,
            side="buy_to_open",
            order_type="limit",
            limit_price=5.0,
            client_order_id="test_strategy_id",
        )
        print("✅ client_order_id passed correctly")


if __name__ == "__main__":
    unittest.main()
