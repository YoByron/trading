"""
Tests for the research package.

These tests verify the core functionality of the research framework:
- Feature generation
- Data labeling
- Data validation
- Portfolio optimization
- Baseline strategies
- Factor analysis
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


class TestFeatureLibrary:
    """Tests for FeatureLibrary."""

    def test_import(self):
        """Test that FeatureLibrary can be imported."""
        from src.research.alpha import FeatureLibrary

        assert FeatureLibrary is not None

    def test_compute_all_features(self, sample_ohlcv_data):
        """Test feature computation."""
        from src.research.alpha import FeatureLibrary

        feature_lib = FeatureLibrary()
        features = feature_lib.compute_all_features(sample_ohlcv_data)

        # Should have more columns than input
        assert len(features.columns) > len(sample_ohlcv_data.columns)

        # Should have specific feature columns
        assert "rsi" in features.columns
        assert "macd" in features.columns
        assert "atr" in features.columns


class TestAlphaResearcher:
    """Tests for AlphaResearcher."""

    def test_generate_signals(self, sample_ohlcv_data):
        """Test signal generation."""
        from src.research.alpha import AlphaResearcher, FeatureLibrary

        feature_lib = FeatureLibrary()
        features = feature_lib.compute_all_features(sample_ohlcv_data)

        researcher = AlphaResearcher(feature_lib)
        signals = researcher.generate_signals(features, ["momentum", "mean_reversion"])

        assert "alpha_momentum" in signals.columns
        assert "alpha_mean_reversion" in signals.columns


class TestTripleBarrierLabeler:
    """Tests for TripleBarrierLabeler."""

    def test_import(self):
        """Test that TripleBarrierLabeler can be imported."""
        from src.research.labeling import TripleBarrierLabeler

        assert TripleBarrierLabeler is not None

    def test_fit_transform(self, sample_ohlcv_data):
        """Test triple-barrier labeling."""
        from src.research.labeling import TripleBarrierLabeler

        labeler = TripleBarrierLabeler()
        result = labeler.fit_transform(sample_ohlcv_data)

        # Should have labels
        assert len(result.labels) > 0

        # Labels should be -1, 0, or 1
        assert set(result.labels.unique()).issubset({-1, 0, 1})

        # Metadata should exist
        assert "total_samples" in result.metadata


class TestDirectionalLabeler:
    """Tests for DirectionalLabeler."""

    def test_fit_transform(self, sample_ohlcv_data):
        """Test directional labeling."""
        from src.research.labeling import DirectionalLabeler

        labeler = DirectionalLabeler(horizons=[5, 21])
        result = labeler.fit_transform(sample_ohlcv_data)

        assert "direction_5d" in result.labels.columns
        assert "direction_21d" in result.labels.columns


class TestDataValidator:
    """Tests for DataValidator."""

    def test_validate(self, sample_ohlcv_data):
        """Test data validation."""
        from src.research.data_contracts import DataValidator

        validator = DataValidator()
        report = validator.validate(sample_ohlcv_data, symbol="TEST")

        # Should have results
        assert report.total_checks > 0
        assert report.passed_checks >= 0

        # Should have data hash
        assert len(report.data_hash) > 0

    def test_validate_bad_data(self):
        """Test validation catches bad data."""
        from src.research.data_contracts import DataValidator

        # Create data with OHLC violation
        df = pd.DataFrame(
            {
                "Open": [100],
                "High": [95],  # High < Low
                "Low": [105],
                "Close": [100],
                "Volume": [1000000],
            },
            index=pd.date_range("2023-01-01", periods=1),
        )

        validator = DataValidator()
        report = validator.validate(df, symbol="BAD")

        # Should have failed checks
        assert report.failed_checks > 0


class TestPortfolioOptimizer:
    """Tests for PortfolioOptimizer."""

    def test_mean_variance_optimization(self):
        """Test mean-variance optimization."""
        from src.research.portfolio import OptimizationMethod, PortfolioOptimizer

        np.random.seed(42)
        assets = ["SPY", "QQQ", "TLT"]
        expected_returns = pd.Series([0.1, 0.12, 0.05], index=assets)
        cov = pd.DataFrame(
            np.eye(3) * 0.04,
            index=assets,
            columns=assets,
        )

        optimizer = PortfolioOptimizer()
        result = optimizer.optimize(expected_returns, cov, method=OptimizationMethod.MEAN_VARIANCE)

        # Weights should sum to 1
        assert abs(result.weights.sum() - 1.0) < 0.01

        # All weights should be non-negative (long-only)
        assert all(result.weights >= -0.01)

    def test_risk_parity_optimization(self):
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

        # Weights should sum to 1
        assert abs(result.weights.sum() - 1.0) < 0.01


class TestBaselineStrategies:
    """Tests for baseline strategies."""

    def test_buy_and_hold(self, sample_ohlcv_data):
        """Test buy and hold baseline."""
        from src.research.baselines import BuyAndHoldBaseline

        strategy = BuyAndHoldBaseline()
        result = strategy.backtest(sample_ohlcv_data)

        # Should have results
        assert result.total_return != 0 or len(sample_ohlcv_data) < 2
        assert len(result.equity_curve) == len(sample_ohlcv_data)

    def test_moving_average_crossover(self, sample_ohlcv_data):
        """Test MA crossover baseline."""
        from src.research.baselines import MovingAverageCrossover

        strategy = MovingAverageCrossover(fast_period=20, slow_period=50)
        result = strategy.backtest(sample_ohlcv_data)

        assert result.strategy_name == "MA Cross (20/50)"
        assert len(result.equity_curve) == len(sample_ohlcv_data)

    def test_baseline_comparison(self, sample_ohlcv_data):
        """Test running all baselines."""
        from src.research.baselines import run_baseline_comparison

        results = run_baseline_comparison(sample_ohlcv_data, include_all=False)

        # Should have multiple strategies
        assert len(results) >= 5

        # Should have required columns
        assert "strategy_name" in results.columns
        assert "sharpe_ratio" in results.columns


class TestFactorModel:
    """Tests for FactorModel."""

    def test_calculate_exposures(self):
        """Test factor exposure calculation."""
        from src.research.factors import FactorModel

        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=100, freq="D")

        # Market factor
        market = pd.Series(np.random.randn(100) * 0.01, index=dates, name="market")

        # Portfolio with beta = 1.2
        portfolio = 1.2 * market + np.random.randn(100) * 0.005
        portfolio = pd.Series(portfolio.values, index=dates)

        factor_returns = pd.DataFrame({"market": market})

        model = FactorModel()
        exposures = model.calculate_exposures(portfolio, factor_returns)

        # Should have market exposure
        assert "market" in exposures

        # Beta should be close to 1.2
        assert abs(exposures["market"].exposure - 1.2) < 0.5

    def test_synthetic_factor_generator(self):
        """Test synthetic factor generation."""
        from src.research.factors import SyntheticFactorGenerator

        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=300, freq="D")
        prices = pd.DataFrame(
            {
                "SPY": 100 * (1 + np.random.randn(300).cumsum() * 0.01),
                "QQQ": 100 * (1 + np.random.randn(300).cumsum() * 0.012),
                "TLT": 100 * (1 + np.random.randn(300).cumsum() * 0.005),
            },
            index=dates,
        )

        generator = SyntheticFactorGenerator()
        factors = generator.generate_all_factors(prices, market_symbol="SPY")

        assert "market" in factors.columns
        assert len(factors) > 0


class TestExperimentTracker:
    """Tests for ExperimentTracker."""

    def test_start_and_end_run(self, tmp_path):
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
        tracker.end_run()

        # Check run was saved
        runs = tracker.list_runs()
        assert len(runs) == 1
        assert runs[0]["metrics"]["accuracy"] == 0.85


class TestIntegration:
    """Integration tests for the research package."""

    def test_full_workflow(self, sample_ohlcv_data):
        """Test complete research workflow."""
        from src.research import (
            AlphaResearcher,
            DataValidator,
            FeatureLibrary,
            TripleBarrierLabeler,
            run_baseline_comparison,
        )

        # 1. Validate data
        validator = DataValidator()
        report = validator.validate(sample_ohlcv_data, "TEST")
        assert report.total_checks > 0

        # 2. Generate features
        feature_lib = FeatureLibrary()
        features = feature_lib.compute_all_features(sample_ohlcv_data)
        assert len(features.columns) > 10

        # 3. Create labels
        labeler = TripleBarrierLabeler()
        labels = labeler.fit_transform(sample_ohlcv_data)
        assert len(labels.labels) > 0

        # 4. Generate signals
        researcher = AlphaResearcher(feature_lib)
        signals = researcher.generate_signals(features, ["momentum"])
        assert "alpha_momentum" in signals.columns

        # 5. Run baselines
        baselines = run_baseline_comparison(sample_ohlcv_data, include_all=False)
        assert len(baselines) >= 5
