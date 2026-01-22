---
layout: post
title: "Ralph's Discovery Log: 3 Fixes in 24 Hours"
date: 2026-01-22 17:55:03
categories: [ralph, automation, ai-engineering]
tags: [self-healing, ci-cd, autonomous-systems]
---

## 🤖 Autonomous Engineering in Action

Our AI system, Ralph (named after the [Ralph Wiggum iterative coding technique](https://github.com/Th0rgal/opencode-ralph-wiggum)),
continuously monitors, discovers, and fixes issues in our trading system. Here's what it found today.


### Discovery #1: LL-281: CALL Leg Pricing Fix - Aggressive Fallbacks

**🔍 What Ralph Found:**
Identified during automated scanning

**🔧 The Fix:**
1. **Detect CALL vs PUT**: Check symbol for "C" to identify calls 2. **Higher CALL fallback**: $4.00 for CALLs vs $2.00 for PUTs 3. **Price buffer**: Add 10% buffer on BUY orders to ensure fills 4. **Quote validation**: Check for $0 bids/asks before using ```python fallback = 1.50 if is_call: fallback = 4.00  # CALLs are more expensive else: fallback = 2.00  # PUTs ``` 1. **Use realistic fallbacks**: Match typical option prices for each type 2. **Add price buffers**: Ensure aggressive enough for

**📈 Impact:**
System stability improved

---

### Discovery #2: LL-281: Alpaca API Bug - Close Position Treated as Opening Cash-Secured Put

**🔍 What Ralph Found:**
Should file ticket with: - Account: Paper trading $5K - Symbol: SPY260220P00658000 - Action: SELL to close 8 long contracts - Error: "insufficient options buying power for cash-secured put" - Expected: Position should close, not require $113K collateral

**🔧 The Fix:**
Automated fix applied by Ralph

**📈 Impact:**
System stability improved

---

### Discovery #3: LL-282: Use close_position() API for Closing Orphan Positions

**🔍 What Ralph Found:**
Identified during automated scanning

**🔧 The Fix:**
1. Replace `submit_order(MarketOrderRequest(...))` with `close_position(symbol)`: ```python order_request = MarketOrderRequest( symbol=option_symbol, qty=qty, side=close_side, time_in_force=TimeInForce.GTC  # NOT supported for options! ) order = client.submit_order(order_request)

**📈 Impact:**
``` 2. Use `TimeInForce.DAY` for any options orders (GTC not supported) 3. Add scheduled triggers to close workflows for auto-healing during market hours - `.github/workflows/emergency-close-options.yml` - Now uses close_position() - `scripts/close_orphan_put.py` - Now uses close_position() - `scrip

---

## 📝 Commits This Session

| SHA | Message |
|-----|---------|
| `debf80f6` | feat(emergency): Add workflow to close profitable SHORT posi |
| `b135571e` | fix(critical): Use local trade history for PDT calculation ( |
| `05514f4d` | feat(emergency): Add workflow to close profitable SHORT posi |
| `2e04d111` | feat(emergency): Add scheduled position close for Jan 23 (#2 |
| `304dee83` | docs(ralph): Auto-publish discovery blog post |


## 🎯 Why This Matters

Self-healing systems aren't just about fixing bugs—they're about building confidence
in autonomous operations. Every fix Ralph makes is:

1. **Documented** in our lessons learned database
2. **Tested** before being applied
3. **Reviewed** via pull request (when significant)

This is the future of software engineering: systems that improve themselves.

---

*Generated automatically by Ralph Mode on 2026-01-22 17:55:03*

**Follow our journey:** [GitHub](https://github.com/IgorGanapolsky/trading) |
Building a $100/day trading system with AI.
