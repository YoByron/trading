from types import SimpleNamespace

from src.safety.regime_entry_gate import evaluate_regime_entry


def _snapshot(
    *,
    regime_id: int,
    label: str = "calm",
    confidence: float = 0.5,
    vix_level: float = 19.0,
    transition_prediction=None,
):
    return SimpleNamespace(
        regime_id=regime_id,
        label=label,
        confidence=confidence,
        vix_level=vix_level,
        transition_prediction=transition_prediction,
    )


def test_unknown_regime_fails_closed():
    decision = evaluate_regime_entry(
        _snapshot(regime_id=-1, label="unknown", confidence=0.0, vix_level=0.0)
    )

    assert not decision.allowed
    assert decision.level == "block"
    assert "unknown regime" in decision.reason


def test_low_confidence_calm_with_normal_vix_reaches_downstream_gates():
    decision = evaluate_regime_entry(
        _snapshot(regime_id=0, label="calm", confidence=0.15, vix_level=19.5)
    )

    assert decision.allowed
    assert decision.level == "warn"
    assert "LOW CONFIDENCE ALLOWED" in decision.reason


def test_low_confidence_without_normal_vix_fails_closed():
    decision = evaluate_regime_entry(
        _snapshot(regime_id=0, label="calm", confidence=0.15, vix_level=0.0)
    )

    assert not decision.allowed
    assert decision.level == "block"
    assert "without normal VIX confirmation" in decision.reason


def test_volatile_regime_blocks_even_with_high_confidence():
    decision = evaluate_regime_entry(
        _snapshot(regime_id=2, label="volatile", confidence=0.95, vix_level=24.0)
    )

    assert not decision.allowed
    assert decision.level == "block"
    assert "volatile regime" in decision.reason


def test_predicted_transition_to_spike_blocks():
    transition = SimpleNamespace(
        transition_detected=True,
        predicted_regime="spike",
        transition_probability=0.67,
    )
    decision = evaluate_regime_entry(
        _snapshot(
            regime_id=0,
            label="calm",
            confidence=0.8,
            vix_level=18.0,
            transition_prediction=transition,
        )
    )

    assert not decision.allowed
    assert decision.level == "block"
    assert "REGIME TRANSITION" in decision.reason
