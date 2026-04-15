"""
Tests for src/utils/self_healing.py

Covers: load_state, save_state, get_anthropic_api_key, with_retry decorator,
        _clear_* helpers, clear_cached_resources, health_check, self_heal,
        is_fallback_mode, clear_fallback_mode, get_error_summary.
"""

import json
import time
from contextlib import suppress
from unittest.mock import MagicMock, patch

import pytest

import src.utils.self_healing as sh


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolated_state_file(tmp_path, monkeypatch):
    """Redirect STATE_FILE to a temp directory so tests never touch data/."""
    fake_state = tmp_path / "agent_state.json"
    monkeypatch.setattr(sh, "STATE_FILE", fake_state)
    yield fake_state


# ---------------------------------------------------------------------------
# get_anthropic_api_key (line 25)
# ---------------------------------------------------------------------------


def test_get_anthropic_api_key_primary(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "key-primary")
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)
    assert sh.get_anthropic_api_key() == "key-primary"


def test_get_anthropic_api_key_fallback(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("CLAUDE_API_KEY", "key-fallback")
    assert sh.get_anthropic_api_key() == "key-fallback"


def test_get_anthropic_api_key_none(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)
    assert sh.get_anthropic_api_key() is None


# ---------------------------------------------------------------------------
# load_state (lines 30-36)
# ---------------------------------------------------------------------------


def test_load_state_missing_file(isolated_state_file):
    """When STATE_FILE does not exist, return default structure."""
    assert not isolated_state_file.exists()
    state = sh.load_state()
    assert state == {"errors": [], "last_heal": None}


def test_load_state_valid_file(isolated_state_file):
    data = {"errors": [{"id": "x"}], "last_heal": 12345.0}
    isolated_state_file.write_text(json.dumps(data))
    state = sh.load_state()
    assert state["last_heal"] == 12345.0
    assert len(state["errors"]) == 1


def test_load_state_corrupt_file(isolated_state_file):
    """Corrupt JSON returns default structure."""
    isolated_state_file.write_text("not-json{{")
    state = sh.load_state()
    assert state == {"errors": [], "last_heal": None}


# ---------------------------------------------------------------------------
# save_state (lines 41-45)
# ---------------------------------------------------------------------------


def test_save_state_creates_file(isolated_state_file):
    sh.save_state({"errors": [], "last_heal": None})
    assert isolated_state_file.exists()
    saved = json.loads(isolated_state_file.read_text())
    assert saved["errors"] == []


def test_save_state_handles_write_error():
    """If write fails, save_state logs but does not raise."""
    with patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
        # Should not raise
        sh.save_state({"errors": []})


# ---------------------------------------------------------------------------
# with_retry decorator (lines 61-105)
# ---------------------------------------------------------------------------


def test_with_retry_succeeds_on_first_attempt():
    call_count = {"n": 0}

    @sh.with_retry(max_attempts=3, backoff=0.0)
    def always_ok():
        call_count["n"] += 1
        return "ok"

    result = always_ok()
    assert result == "ok"
    assert call_count["n"] == 1


def test_with_retry_retries_and_eventually_succeeds():
    attempts = {"n": 0}

    @sh.with_retry(max_attempts=3, backoff=0.0)
    def fails_twice():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise ValueError("transient")
        return "recovered"

    with patch("src.utils.self_healing.time.sleep"):
        result = fails_twice()

    assert result == "recovered"
    assert attempts["n"] == 3


def test_with_retry_raises_after_all_attempts_exhausted():
    @sh.with_retry(max_attempts=2, backoff=0.0)
    def always_fails():
        raise RuntimeError("boom")

    with patch("src.utils.self_healing.time.sleep"):
        with pytest.raises(RuntimeError, match="boom"):
            always_fails()


def test_with_retry_logs_errors_to_state(isolated_state_file):
    @sh.with_retry(max_attempts=2, backoff=0.0)
    def fails():
        raise ValueError("oops")

    with patch("src.utils.self_healing.time.sleep"):
        with pytest.raises(ValueError):
            fails()

    state = sh.load_state()
    assert len(state["errors"]) >= 1
    assert state["errors"][0]["function"] == "fails"
    assert "oops" in state["errors"][0]["msg"]


def test_with_retry_only_catches_specified_exceptions():
    @sh.with_retry(max_attempts=3, backoff=0.0, exceptions=(ValueError,))
    def raises_type_error():
        raise TypeError("wrong type")

    with patch("src.utils.self_healing.time.sleep"):
        with pytest.raises(TypeError):
            raises_type_error()


def test_with_retry_exponential_backoff():
    sleep_calls = []

    @sh.with_retry(max_attempts=3, backoff=1.0)
    def always_fails():
        raise ValueError("fail")

    with patch("src.utils.self_healing.time.sleep", side_effect=lambda d: sleep_calls.append(d)):
        with pytest.raises(ValueError):
            always_fails()

    # backoff * 2^(attempt-1): 1.0, 2.0
    assert len(sleep_calls) == 2
    assert sleep_calls[0] == pytest.approx(1.0)
    assert sleep_calls[1] == pytest.approx(2.0)


def test_with_retry_preserves_function_name():
    @sh.with_retry()
    def my_special_function():
        return 1

    assert my_special_function.__name__ == "my_special_function"


def test_with_retry_zero_attempts_returns_none():
    """Cover line 101: when max_attempts=0, while loop never runs, returns None."""

    @sh.with_retry(max_attempts=0)
    def should_not_be_called():
        return "unreachable"

    result = should_not_be_called()
    assert result is None


# ---------------------------------------------------------------------------
# _clear_sentiment_cache (lines 110-117)
# ---------------------------------------------------------------------------


def test_clear_sentiment_cache_no_module():
    """If src.utils.sentiment is not importable, return False gracefully."""
    with patch.dict("sys.modules", {"src.utils.sentiment": None}):
        result = sh._clear_sentiment_cache()
    # Result is False because import is suppressed
    assert isinstance(result, bool)


def test_clear_sentiment_cache_with_cache_clear():
    """When sentiment module is importable and analyzer has cache_clear, return True."""
    mock_analyzer = MagicMock()
    mock_analyzer.cache_clear = MagicMock()
    mock_sentiment = MagicMock()
    mock_sentiment._get_analyzer = mock_analyzer

    # Patch the import inside the function by injecting into sys.modules
    # and also patching 'src.utils' so `from src.utils import sentiment` resolves
    import sys
    import types

    fake_src_utils = types.ModuleType("src.utils")
    fake_src_utils.sentiment = mock_sentiment

    original = sys.modules.copy()
    sys.modules["src.utils.sentiment"] = mock_sentiment
    # Ensure src.utils exists so the from-import works
    if "src.utils" not in sys.modules:
        sys.modules["src.utils"] = fake_src_utils

    try:
        result = sh._clear_sentiment_cache()
    finally:
        # Restore only the keys we added/replaced
        for key in list(sys.modules.keys()):
            if key not in original:
                del sys.modules[key]
            elif sys.modules[key] is not original[key]:
                sys.modules[key] = original[key]

    # If the import succeeded and _get_analyzer has cache_clear, should be True
    assert result is True
    mock_analyzer.cache_clear.assert_called_once()


def test_clear_sentiment_cache_analyzer_no_cache_clear():
    """When analyzer exists but has no cache_clear, return False."""
    import sys
    import types

    mock_analyzer = MagicMock(spec=[])  # no cache_clear
    mock_sentiment = types.ModuleType("src.utils.sentiment")
    mock_sentiment._get_analyzer = mock_analyzer

    original = sys.modules.copy()
    sys.modules["src.utils.sentiment"] = mock_sentiment

    try:
        result = sh._clear_sentiment_cache()
    finally:
        for key in list(sys.modules.keys()):
            if key not in original:
                del sys.modules[key]
            elif sys.modules[key] is not original[key]:
                sys.modules[key] = original[key]

    assert result is False


# ---------------------------------------------------------------------------
# _clear_pydantic_shim_cache (lines 122-129)
# ---------------------------------------------------------------------------


def test_clear_pydantic_shim_cache_no_module():
    result = sh._clear_pydantic_shim_cache()
    assert isinstance(result, bool)


def test_clear_pydantic_shim_cache_shim_no_cache_clear():
    """When shim exists but has no cache_clear attribute, return False (line 129)."""
    import src.utils as src_utils_pkg
    import types

    mock_shim = MagicMock(spec=[])  # no cache_clear
    mock_pydantic_compat = types.ModuleType("src.utils.pydantic_compat")
    mock_pydantic_compat.ensure_pydantic_base_settings = mock_shim

    original_attr = getattr(src_utils_pkg, "pydantic_compat", None)
    src_utils_pkg.pydantic_compat = mock_pydantic_compat
    with patch.dict("sys.modules", {"src.utils.pydantic_compat": mock_pydantic_compat}):
        try:
            result = sh._clear_pydantic_shim_cache()
        finally:
            if original_attr is None:
                with suppress(AttributeError):
                    delattr(src_utils_pkg, "pydantic_compat")
            else:
                src_utils_pkg.pydantic_compat = original_attr

    assert result is False


def test_clear_pydantic_shim_cache_with_cache_clear():
    """When pydantic_compat module is importable and shim has cache_clear, return True."""
    import types

    mock_shim = MagicMock()
    mock_shim.cache_clear = MagicMock()
    mock_pydantic_compat = types.ModuleType("src.utils.pydantic_compat")
    mock_pydantic_compat.ensure_pydantic_base_settings = mock_shim

    # Both patch the sys.modules key AND set the attribute on src.utils package
    # so that `from src.utils import pydantic_compat` resolves to our mock
    import src.utils as src_utils_pkg

    original_attr = getattr(src_utils_pkg, "pydantic_compat", None)
    src_utils_pkg.pydantic_compat = mock_pydantic_compat
    with patch.dict("sys.modules", {"src.utils.pydantic_compat": mock_pydantic_compat}):
        try:
            result = sh._clear_pydantic_shim_cache()
        finally:
            if original_attr is None:
                with suppress(AttributeError):
                    delattr(src_utils_pkg, "pydantic_compat")
            else:
                src_utils_pkg.pydantic_compat = original_attr

    assert result is True
    mock_shim.cache_clear.assert_called_once()


# ---------------------------------------------------------------------------
# _clear_mcp_cache (lines 134-144)
# ---------------------------------------------------------------------------


def test_clear_mcp_cache_import_fails():
    """When mcp.client is missing, return False."""
    with patch.dict("sys.modules", {"mcp": None, "mcp.client": None}):
        result = sh._clear_mcp_cache("get_multi_llm_analyzer")
    assert result is False


def test_clear_mcp_cache_factory_missing():
    mock_mcp_client = MagicMock(spec=[])  # no attributes
    mock_mcp = MagicMock()
    mock_mcp.client = mock_mcp_client

    with patch.dict("sys.modules", {"mcp": mock_mcp, "mcp.client": mock_mcp_client}):
        result = sh._clear_mcp_cache("nonexistent_factory")
    assert result is False


def test_clear_mcp_cache_factory_has_cache_clear():
    factory = MagicMock()
    factory.cache_clear = MagicMock()
    mock_mcp_client = MagicMock()
    mock_mcp_client.get_multi_llm_analyzer = factory
    mock_mcp = MagicMock()
    mock_mcp.client = mock_mcp_client

    with patch.dict("sys.modules", {"mcp": mock_mcp, "mcp.client": mock_mcp_client}):
        result = sh._clear_mcp_cache("get_multi_llm_analyzer")

    assert result is True
    factory.cache_clear.assert_called_once()


def test_clear_mcp_cache_factory_no_cache_clear():
    factory = MagicMock(spec=[])  # no cache_clear
    mock_mcp_client = MagicMock()
    mock_mcp_client.some_factory = factory
    mock_mcp = MagicMock()
    mock_mcp.client = mock_mcp_client

    with patch.dict("sys.modules", {"mcp": mock_mcp, "mcp.client": mock_mcp_client}):
        result = sh._clear_mcp_cache("some_factory")

    assert result is False


# ---------------------------------------------------------------------------
# _clear_multi_llm_cache / _clear_alpaca_trader_cache (lines 148, 152)
# ---------------------------------------------------------------------------


def test_clear_multi_llm_cache_delegates():
    with patch.object(sh, "_clear_mcp_cache", return_value=True) as mock_fn:
        result = sh._clear_multi_llm_cache()
    mock_fn.assert_called_once_with("get_multi_llm_analyzer")
    assert result is True


def test_clear_alpaca_trader_cache_delegates():
    with patch.object(sh, "_clear_mcp_cache", return_value=False) as mock_fn:
        result = sh._clear_alpaca_trader_cache()
    mock_fn.assert_called_once_with("get_alpaca_trader")
    assert result is False


# ---------------------------------------------------------------------------
# clear_cached_resources (lines 168-175)
# ---------------------------------------------------------------------------


def test_clear_cached_resources_returns_cleared_names():
    fake_clearers = (
        ("sentiment analyzer", lambda: True),
        ("pydantic BaseSettings shim", lambda: False),
        ("multi-LLM analyzer", lambda: True),
        ("alpaca trader", lambda: False),
    )
    with patch.object(sh, "_CACHE_CLEARERS", fake_clearers):
        cleared = sh.clear_cached_resources()

    assert "sentiment analyzer" in cleared
    assert "multi-LLM analyzer" in cleared
    assert "pydantic BaseSettings shim" not in cleared
    assert "alpaca trader" not in cleared


def test_clear_cached_resources_handles_clearer_exception():
    def boom():
        raise RuntimeError("cache exploded")

    fake_clearers = (("broken", boom),)
    with patch.object(sh, "_CACHE_CLEARERS", fake_clearers):
        cleared = sh.clear_cached_resources()

    assert cleared == []


# ---------------------------------------------------------------------------
# health_check (lines 189-212)
# ---------------------------------------------------------------------------


def test_health_check_passes_when_no_errors(isolated_state_file):
    sh.save_state({"errors": [], "last_heal": None})
    result = sh.health_check(threshold=5)
    assert result is True


def test_health_check_passes_when_errors_below_threshold(isolated_state_file):
    now = time.time()
    errors = [{"ts": now - 10, "id": f"e{i}"} for i in range(3)]
    sh.save_state({"errors": errors, "last_heal": None})
    result = sh.health_check(threshold=5)
    assert result is True


def test_health_check_fails_and_triggers_self_heal(isolated_state_file):
    now = time.time()
    errors = [{"ts": now - 10, "id": f"e{i}"} for i in range(6)]
    sh.save_state({"errors": errors, "last_heal": None})

    with patch.object(sh, "self_heal") as mock_heal:
        result = sh.health_check(threshold=5)

    assert result is False
    mock_heal.assert_called_once()

    # Errors should be cleared after self-heal
    state = sh.load_state()
    assert state["errors"] == []
    assert state["last_heal"] is not None


def test_health_check_ignores_old_errors(isolated_state_file):
    now = time.time()
    # All errors are outside the 1-hour window
    old_errors = [{"ts": now - 7200, "id": f"e{i}"} for i in range(10)]
    sh.save_state({"errors": old_errors, "last_heal": None})

    result = sh.health_check(threshold=5, window_seconds=3600)
    assert result is True


def test_health_check_exact_threshold_triggers_heal(isolated_state_file):
    now = time.time()
    errors = [{"ts": now - 10, "id": f"e{i}"} for i in range(5)]
    sh.save_state({"errors": errors, "last_heal": None})

    with patch.object(sh, "self_heal"):
        result = sh.health_check(threshold=5)

    assert result is False


# ---------------------------------------------------------------------------
# self_heal (lines 225-274)
# ---------------------------------------------------------------------------


def _make_mock_anthropic_module(client_instance):
    """Return a fake 'anthropic' module with Anthropic class returning client_instance."""
    import types

    mock_anthropic = types.ModuleType("anthropic")
    mock_anthropic.Anthropic = MagicMock(return_value=client_instance)
    return mock_anthropic


def test_self_heal_succeeds_with_valid_api_key(isolated_state_file, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock()
    fake_anthropic = _make_mock_anthropic_module(mock_client)

    with (
        patch.dict("sys.modules", {"anthropic": fake_anthropic}),
        patch.object(sh, "clear_cached_resources", return_value=["sentiment analyzer"]),
    ):
        sh.self_heal()

    mock_client.messages.create.assert_called_once()


def test_self_heal_clears_no_caches_when_none_cleared(isolated_state_file, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    mock_client = MagicMock()
    fake_anthropic = _make_mock_anthropic_module(mock_client)

    with (
        patch.dict("sys.modules", {"anthropic": fake_anthropic}),
        patch.object(sh, "clear_cached_resources", return_value=[]),
    ):
        sh.self_heal()  # Should not raise


def test_self_heal_activates_fallback_when_api_key_missing(isolated_state_file, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)

    sh.self_heal()

    state = sh.load_state()
    assert state.get("fallback_mode") is True
    assert "fallback_reason" in state


def test_self_heal_missing_api_key_with_anthropic_importable(isolated_state_file, monkeypatch):
    """Cover lines 234-235: anthropic importable but API key missing -> ValueError raised."""
    import types

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)

    # Make anthropic importable so the code reaches the api_key check (lines 233-235)
    fake_anthropic = types.ModuleType("anthropic")
    fake_anthropic.Anthropic = MagicMock()

    with patch.dict("sys.modules", {"anthropic": fake_anthropic}):
        sh.self_heal()

    state = sh.load_state()
    assert state.get("fallback_mode") is True
    assert "Missing API key" in state.get("fallback_reason", "")


def test_self_heal_activates_fallback_when_client_creation_fails(isolated_state_file, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    import types

    mock_anthropic = types.ModuleType("anthropic")
    mock_anthropic.Anthropic = MagicMock(side_effect=RuntimeError("connection failed"))

    with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
        sh.self_heal()

    state = sh.load_state()
    assert state.get("fallback_mode") is True


def test_self_heal_activates_fallback_when_test_message_fails(isolated_state_file, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = RuntimeError("rate limited")
    fake_anthropic = _make_mock_anthropic_module(mock_client)

    with patch.dict("sys.modules", {"anthropic": fake_anthropic}):
        sh.self_heal()

    state = sh.load_state()
    assert state.get("fallback_mode") is True
    assert "rate limited" in state.get("fallback_reason", "")


def test_self_heal_fallback_save_fails_logs_critical(isolated_state_file, monkeypatch):
    """Cover lines 273-274: when save_state inside fallback also raises, log critical."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)

    import types

    fake_anthropic = types.ModuleType("anthropic")
    fake_anthropic.Anthropic = MagicMock()

    save_call_count = {"n": 0}

    def failing_save(state):
        save_call_count["n"] += 1
        raise OSError("disk full")

    with (
        patch.dict("sys.modules", {"anthropic": fake_anthropic}),
        patch.object(sh, "save_state", side_effect=failing_save),
    ):
        # Should not raise — logs critical instead
        sh.self_heal()

    # save_state was attempted (and failed — lines 273-274 executed)
    assert save_call_count["n"] >= 1


# ---------------------------------------------------------------------------
# is_fallback_mode (lines 279-280)
# ---------------------------------------------------------------------------


def test_is_fallback_mode_false_by_default(isolated_state_file):
    sh.save_state({"errors": [], "last_heal": None})
    assert sh.is_fallback_mode() is False


def test_is_fallback_mode_true_when_set(isolated_state_file):
    sh.save_state({"errors": [], "last_heal": None, "fallback_mode": True})
    assert sh.is_fallback_mode() is True


def test_is_fallback_mode_false_when_explicitly_false(isolated_state_file):
    sh.save_state({"errors": [], "last_heal": None, "fallback_mode": False})
    assert sh.is_fallback_mode() is False


# ---------------------------------------------------------------------------
# clear_fallback_mode (lines 285-289)
# ---------------------------------------------------------------------------


def test_clear_fallback_mode_removes_flag(isolated_state_file):
    sh.save_state(
        {"errors": [], "last_heal": None, "fallback_mode": True, "fallback_reason": "oops"}
    )
    sh.clear_fallback_mode()
    state = sh.load_state()
    assert state["fallback_mode"] is False
    assert "fallback_reason" not in state


def test_clear_fallback_mode_idempotent(isolated_state_file):
    sh.save_state({"errors": [], "last_heal": None})
    sh.clear_fallback_mode()  # Should not raise even if already clear
    assert sh.is_fallback_mode() is False


# ---------------------------------------------------------------------------
# get_error_summary (lines 302-304)
# ---------------------------------------------------------------------------


def test_get_error_summary_empty_state(isolated_state_file):
    sh.save_state({"errors": [], "last_heal": None})
    assert sh.get_error_summary() == []


def test_get_error_summary_returns_last_n(isolated_state_file):
    errors = [{"id": str(i)} for i in range(20)]
    sh.save_state({"errors": errors, "last_heal": None})
    summary = sh.get_error_summary(limit=5)
    assert len(summary) == 5
    # Should return the LAST 5
    assert summary[-1]["id"] == "19"


def test_get_error_summary_fewer_than_limit(isolated_state_file):
    errors = [{"id": "a"}, {"id": "b"}]
    sh.save_state({"errors": errors, "last_heal": None})
    summary = sh.get_error_summary(limit=10)
    assert len(summary) == 2


def test_get_error_summary_default_limit(isolated_state_file):
    errors = [{"id": str(i)} for i in range(15)]
    sh.save_state({"errors": errors, "last_heal": None})
    summary = sh.get_error_summary()
    assert len(summary) == 10
