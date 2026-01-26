---
layout: post
title: "Engineering Log: LL-309: Iron Condor Optimal Control Rese (+2 more)"
date: 2026-01-26 07:24:06
categories: [engineering, lessons-learned, ai-trading]
tags: [success, left-biased, options, put]
---

**Monday, January 26, 2026** (Eastern Time)

Building an autonomous AI trading system means things break. Here's what we discovered, fixed, and learned today.


## LL-309: Iron Condor Optimal Control Research

**The Problem:** **Date**: 2026-01-25 **Category**: Research / Strategy Optimization **Source**: arXiv:2501.12397 - "Stochastic Optimal Control of Iron Condor Portfolios"

**What We Did:** - **Finding**: "Asymmetric, left-biased Iron Condor portfolios with τ = T are optimal in SPX markets" - **Meaning**: Put spread should be closer to current price than call spread - **Why**: Markets have negative skew (crashes more likely than rallies)

**The Takeaway:** - **Left-biased portfolios**: Hold to expiration (τ = T) is optimal - **Non-left-biased portfolios**: Exit at 50-75% of duration

---

## LL-277: Iron Condor Optimization Research - 86% Win Rate Strategy

**The Problem:** **Date**: January 21, 2026 **Category**: strategy, research, optimization **Severity**: HIGH

**What We Did:** - [Options Trading IQ: Iron Condor Success Rate](https://optionstradingiq.com/iron-condor-success-rate/) - [Project Finance: Iron Condor Management (71,417 trades)](https://www.projectfinance.com/iron-condor-management/) | Short Strike Delta | Win Rate |

**The Takeaway:** |-------------------|----------| | **10-15 delta** | **86%** |

---

## LL-298: Invalid Option Strikes Causing CALL Legs to Fail

**The Problem:** See full details in lesson ll_298_invalid_strikes_call_legs_fail_jan23

**What We Did:** - Added `round_to_5()` function to `calculate_strikes()` - All strikes now rounded to nearest $5 multiple - Commit: `8b3e411` (PR pending merge) 1. Always round SPY strikes to $5 increments 2. Verify ALL 4 legs fill before considering trade complete 3. Add validation that option symbols exist before submitting orders 4. Log when any leg fails to fill - LL-297: Incomplete iron condor crisis (PUT-only positions) - LL-281: CALL leg pricing fallback iron_condor, options, strikes, call_legs, validati

**The Takeaway:** Risk reduced and system resilience improved

---

## Code Changes

These commits shipped today ([view on GitHub](https://github.com/IgorGanapolsky/trading/commits/main)):

| Commit | Description |
|--------|-------------|
| [cf0dc6b2](https://github.com/IgorGanapolsky/trading/commit/cf0dc6b2) | chore(ralph): CI iteration ✅ |
| [3379fcb9](https://github.com/IgorGanapolsky/trading/commit/3379fcb9) | feat(rag): Add LL-312 lesson - Workflow concurrency aud |
| [9d772046](https://github.com/IgorGanapolsky/trading/commit/9d772046) | docs(ralph): Auto-publish discovery blog post |
| [f8bf9ed7](https://github.com/IgorGanapolsky/trading/commit/f8bf9ed7) | docs(ralph): Auto-publish discovery blog post |
| [32f72e59](https://github.com/IgorGanapolsky/trading/commit/32f72e59) | feat(ml): Complete ML improvements (ML-IMP-1, ML-IMP-3, |


## Why We Share This

Every bug is a lesson. Every fix makes the system stronger. We're building in public because:

1. **Transparency builds trust** - See exactly how an autonomous trading system evolves
2. **Failures teach more than successes** - Our mistakes help others avoid the same pitfalls
3. **Documentation prevents regression** - Writing it down means we won't repeat it

---

*This is part of our journey building an AI-powered iron condor trading system targeting financial independence.*

**Resources:**
- [Source Code](https://github.com/IgorGanapolsky/trading)
- [Strategy Guide](https://igorganapolsky.github.io/trading/2026/01/21/iron-condors-ai-trading-complete-guide.html)
- [The Silent 74 Days](https://igorganapolsky.github.io/trading/2026/01/07/the-silent-74-days.html) - How we built a system that did nothing
