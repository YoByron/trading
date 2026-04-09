from __future__ import annotations

from src.utils import yfinance_wrapper


class _FakeYFinance:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def download(self, tickers, **kwargs):
        self.calls.append({"tickers": tickers, **kwargs})
        return {"ok": True}


def test_download_omits_period_when_start_or_end_are_explicit(monkeypatch) -> None:
    fake = _FakeYFinance()
    monkeypatch.setattr(yfinance_wrapper, "_try_import_yfinance", lambda: fake)

    result = yfinance_wrapper.download(
        ["^VIX", "^VVIX", "TLT"],
        start="2026-01-01",
        end="2026-04-09",
        progress=False,
    )

    assert result == {"ok": True}
    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["tickers"] == ["^VIX", "^VVIX", "TLT"]
    assert call["start"] == "2026-01-01"
    assert call["end"] == "2026-04-09"
    assert "period" not in call


def test_download_keeps_period_when_no_explicit_window(monkeypatch) -> None:
    fake = _FakeYFinance()
    monkeypatch.setattr(yfinance_wrapper, "_try_import_yfinance", lambda: fake)

    yfinance_wrapper.download("^VIX", period="5d", interval="1h", progress=False)

    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["tickers"] == "^VIX"
    assert call["period"] == "5d"
    assert call["interval"] == "1h"
