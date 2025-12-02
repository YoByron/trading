"""
Comprehensive tests for the research package.

Tests all research modules:
- Factors (returns, volatility, volume, technicals, cross-sectional)
- Labeling (directional, triple-barrier, volatility)
- Baselines (buy-and-hold, equal-weight, momentum, SMA cross)
- Portfolio optimization (mean-variance, risk parity, Kelly)
- Experiments (tracking, model registry)
- Alpha (features, signals)
"""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=300, freq="D")
    close = 100 * (1 + np.random.randn(300).cumsum() * 0.01)

    df = pd.DataFrame(
        {
            "Open": close * (1 + np.random.randn(300) * 0.005),
            "High": close * (1 + np.abs(np.random.randn(300)) * 0.01),
            "Low": close * (1 - np.abs(np.random.randn(300)) * 0.01),
            "Close": close,
            "Volume": np.random.randint(1000000, 10000000, 300),
        },
        index=dates,
    )
    return df


class TestFactors:
    """Tests for factor computation modules."""

    def test_calculate_returns(self, sample_ohlcv_data):
        """Test return calculations."""
        from src.research.factors import calculate_returns

        returns = calculate_returns(sample_ohlcv_data["Close"])
        assert len(returns) == len(sample_ohlcv_data)
        assert pd.isna(returns.iloc[0])  # First value is NaN

    def test_calculate_multi_horizon_returns(self, sample_ohlcv_data):
        """Test multi-horizon return calculations."""
        from src.research.factors import calculate_multi_horizon_returns

        returns = calculate_multi_horizon_returns(
            sample_ohlcv_data["Close"], horizons=["1d", "1w", "1mo"]
        )
        assert "returns_1d" in returns.columns
        assert "returns_1w" in returns.columns
        assert "returns_1mo" in returns.columns

    def test_calculate_volatility(self, sample_ohlcv_data):
        """Test volatility calculations."""
        from src.research.factors import calculate_realized_volatility

        vol = calculate_realized_volatility(sample_ohlcv_data["Close"], window=20)
        assert len(vol) == len(sample_ohlcv_data)
        assert vol.dropna().min() >= 0

    def test_calculate_rsi(self, sample_ohlcv_data):
        """Test RSI calculation."""
        from src.research.factors import calculate_rsi

        rsi = calculate_rsi(sample_ohlcv_data["Close"])
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_calculate_macd(self, sample_ohlcv_data):
        """Test MACD calculation."""
        from src.research.factors import calculate_macd

        macd_result = calculate_macd(sample_ohlcv_data["Close"])
        assert "macd" in macd_result
        assert "signal" in macd_result
        assert "histogram" in macd_result
        assert len(macd_result["macd"]) == len(sample_ohlcv_data)

    def test_calculate_bollinger_bands(self, sample_ohlcv_data):
        """Test Bollinger Bands calculation."""
        from src.research.factors import calculate_bollinger_bands

        bb = calculate_bollinger_bands(sample_ohlcv_data["Close"])
        assert "upper" in bb
        assert "lower" in bb
        assert "middle" in bb


class TestLabeling:
    """Tests for labeling modules."""

    def test_create_directional_labels(self, sample_ohlcv_data):
        """Test directional label creation."""
        from src.research.labeling import create_directional_labels

        returns = sample_ohlcv_data["Close"].pct_change()
        labels = create_directional_labels(returns, horizons=["1d", "1w"])
        assert "label_1d" in labels.columns
        assert "label_1w" in labels.columns

    def test_create_volatility_labels(self, sample_ohlcv_data):
        """Test volatility label creation."""
        from src.research.labeling import create_volatility_labels

        returns = sample_ohlcv_data["Close"].pct_change()
        labels = create_volatility_labels(returns, window=20)
        assert len(labels) == len(sample_ohlcv_data)
        valid_labels = labels.dropna()
        assert (valid_labels >= 0).all()

    def test_create_triple_barrier_labels(self, sample_ohlcv_data):
        """Test triple-barrier label creation."""
        from src.research.labeling import create_triple_barrier_labels

        labels = create_triple_barrier_labels(
            sample_ohlcv_data["Close"],
            upper_barrier=0.05,
            lower_barrier=-0.05,
            max_holding_period=20,
        )
        assert len(labels) == len(sample_ohlcv_data)


class TestBaselines:
    """Tests for baseline strategies."""

    def test_buy_and_hold_strategy(self, sample_ohlcv_data):
        """Test buy-and-hold strategy."""
        from src.research.baselines import BuyAndHoldStrategy

        strategy = BuyAndHoldStrategy()
        assert strategy.get_name() == "Buy-and-Hold"

    def test_equal_weight_strategy(self):
        """Test equal-weight strategy."""
        from src.research.baselines import EqualWeightStrategy

        np.random.seed(42)

        strategy = EqualWeightStrategy(symbols=["SPY", "QQQ", "TLT"])
        name = strategy.get_name()
        assert "Equal-Weight" in name

    def test_momentum_strategy(self, sample_ohlcv_data):
        """Test momentum strategy."""
        from src.research.baselines import MomentumStrategy

        strategy = MomentumStrategy(lookback=20)
        name = strategy.get_name()
        assert "Momentum" in name
        assert "20" in name

    def test_sma_cross_strategy(self, sample_ohlcv_data):
        """Test SMA crossover strategy."""
        from src.research.baselines import SMACrossStrategy

        strategy = SMACrossStrategy(short_window=20, long_window=50)
        assert strategy.get_name() == "SMA Cross (20/50)"


class TestPortfolio:
    """Tests for portfolio optimization."""

    def test_portfolio_optimizer_mean_variance(self):
        """Test mean-variance optimization."""
        from src.research.portfolio import OptimizationMethod, PortfolioOptimizer

        np.random.seed(42)
        assets = ["SPY", "QQQ", "TLT"]
        expected_returns = pd.Series([0.1, 0.12, 0.05], index=assets)
        cov = pd.DataFrame(np.eye(3) * 0.04, index=assets, columns=assets)

        optimizer = PortfolioOptimizer()
        result = optimizer.optimize(expected_returns, cov, method=OptimizationMethod.MEAN_VARIANCE)

        assert abs(result.weights.sum() - 1.0) < 0.01
        assert all(result.weights >= -0.01)

    def test_portfolio_optimizer_risk_parity(self):
        """Test risk parity optimization."""
        from src.research.portfolio import OptimizationMethod, PortfolioOptimizer

        assets = ["SPY", "TLT", "GLD"]
        expected_returns = pd.Series([0.08, 0.04, 0.06], index=assets)
        cov = pd.DataFrame(
            [[0.04, 0.01, 0.005], [0.01, 0.01, 0.002], [0.005, 0.002, 0.02]],
            index=assets,
            columns=assets,
        )

        optimizer = PortfolioOptimizer()
        result = optimizer.optimize(expected_returns, cov, method=OptimizationMethod.RISK_PARITY)

        assert abs(result.weights.sum() - 1.0) < 0.01

    def test_kelly_fraction(self):
        """Test Kelly fraction calculation."""
        from src.research.portfolio import calculate_half_kelly, calculate_kelly_fraction

        kelly = calculate_kelly_fraction(expected_return=0.10, volatility=0.20)
        half_kelly = calculate_half_kelly(expected_return=0.10, volatility=0.20)

        assert kelly > 0
        assert half_kelly == kelly / 2


class TestExperiments:
    """Tests for experiment tracking."""

    def test_experiment_tracker(self, tmp_path):
        """Test experiment tracking."""
        from src.research.experiments import ExperimentConfig, ExperimentTracker

        tracker = ExperimentTracker(tracking_dir=str(tmp_path / "experiments"))

        config = ExperimentConfig(
            name="test_experiment",
            hyperparameters={"learning_rate": 0.001},
        )

        run = tracker.start_run("test", config)
        assert run.run_id is not None

        tracker.log_metric("accuracy", 0.85)
        tracker.log_metric("sharpe", 1.5)
        tracker.end_run()

        runs = tracker.list_runs()
        assert len(runs) == 1
        assert runs[0]["metrics"]["accuracy"] == 0.85
        assert runs[0]["metrics"]["sharpe"] == 1.5

    def test_model_registry(self, tmp_path):
        """Test model registry."""
        from src.research.experiments import ModelRegistry, ModelStage

        registry = ModelRegistry(registry_dir=str(tmp_path / "registry"))

        # Use a simple dict as model (picklable)
        model = {"weights": [1.0, 2.0, 3.0], "bias": 0.5}

        version = registry.register_model(
            "test_model",
            model,
            metrics={"sharpe": 1.5},
            description="Test model",
        )

        assert version.version == 1
        assert version.stage == ModelStage.DEVELOPMENT

        registry.transition_stage("test_model", 1, ModelStage.PRODUCTION)
        loaded = registry.load_model("test_model", stage=ModelStage.PRODUCTION)

        assert loaded["weights"] == [1.0, 2.0, 3.0]
        assert loaded["bias"] == 0.5


class TestAlpha:
    """Tests for alpha research modules."""

    def test_feature_library(self, sample_ohlcv_data):
        """Test feature library."""
        from src.research.alpha import FeatureLibrary

        lib = FeatureLibrary()
        features = lib.compute_all(sample_ohlcv_data)

        assert len(features.columns) > 20
        assert "rsi" in features.columns
        assert "macd" in features.columns

    def test_signal_generator(self, sample_ohlcv_data):
        """Test signal generation."""
        from src.research.alpha import FeatureLibrary, SignalGenerator

        lib = FeatureLibrary()
        features = lib.compute_all(sample_ohlcv_data)

        gen = SignalGenerator()
        mom_signal = gen.generate_momentum_signal(features, lookback=20)

        assert mom_signal.name == "momentum_20"
        assert len(mom_signal.signal) == len(sample_ohlcv_data)

    def test_combine_signals(self, sample_ohlcv_data):
        """Test signal combination."""
        from src.research.alpha import FeatureLibrary, SignalGenerator, combine_signals

        lib = FeatureLibrary()
        features = lib.compute_all(sample_ohlcv_data)

        gen = SignalGenerator()
        signals = [
            gen.generate_momentum_signal(features, lookback=20),
            gen.generate_mean_reversion_signal(features, lookback=5),
        ]

        combined = combine_signals(signals, method="equal")
        assert combined.name == "combined_alpha"
        assert len(combined.signal) == len(sample_ohlcv_data)


class TestDataContracts:
    """Tests for data contracts."""

    def test_signal_snapshot(self):
        """Test SignalSnapshot creation."""
        from src.research.data_contracts import SignalSnapshot

        snapshot = SignalSnapshot(
            timestamp=pd.Timestamp("2023-01-01"),
            symbol="SPY",
            features=pd.Series({"momentum": 0.5, "rsi": 65.0}),
            metadata={"source": "test"},
        )

        assert snapshot.symbol == "SPY"
        data = snapshot.to_dict()
        restored = SignalSnapshot.from_dict(data)
        assert restored.symbol == "SPY"

    def test_future_returns(self):
        """Test FutureReturns creation."""
        from src.research.data_contracts import FutureReturns

        returns = FutureReturns(
            symbol="SPY",
            timestamp=pd.Timestamp("2023-01-01"),
            returns_1d=0.01,
            returns_1w=0.03,
        )

        assert returns.returns_1d == 0.01
        data = returns.to_dict()
        restored = FutureReturns.from_dict(data)
        assert restored.returns_1w == 0.03


class TestIntegration:
    """Integration tests for the research package."""

    def test_full_research_workflow(self, sample_ohlcv_data, tmp_path):
        """Test complete research workflow."""
        from src.research.alpha import FeatureLibrary, SignalGenerator
        from src.research.baselines import BuyAndHoldStrategy
        from src.research.experiments import ExperimentConfig, ExperimentTracker
        from src.research.factors import calculate_returns
        from src.research.labeling import create_directional_labels

        returns = calculate_returns(sample_ohlcv_data["Close"])
        assert len(returns) > 0

        lib = FeatureLibrary()
        features = lib.compute_all(sample_ohlcv_data)
        assert len(features.columns) > 10

        labels = create_directional_labels(returns, horizons=["1d", "1w"])
        assert "label_1d" in labels.columns

        gen = SignalGenerator()
        signal = gen.generate_momentum_signal(features, lookback=20)
        assert len(signal.signal) > 0

        strategy = BuyAndHoldStrategy()
        assert strategy.get_name() == "Buy-and-Hold"

        tracker = ExperimentTracker(tracking_dir=str(tmp_path / "exp"))
        config = ExperimentConfig(name="test", hyperparameters={"lookback": 20})
        tracker.start_run("momentum_test", config)
        tracker.log_metric("sharpe", 1.2)
        tracker.end_run()

        runs = tracker.list_runs()
        assert len(runs) == 1
