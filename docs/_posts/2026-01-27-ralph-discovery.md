---
layout: post
title: "Engineering Log: LL-309: Iron Condor Optimal Control Rese (+2 more)"
date: 2026-01-27 11:19:31
categories: [engineering, lessons-learned, ai-trading]
tags: [left-biased, dead, code, detected]
---

**Tuesday, January 27, 2026** (Eastern Time)

Building an autonomous AI trading system means things break. Here's what we discovered, fixed, and learned today.


## LL-309: Iron Condor Optimal Control Research

**The Problem:** **Date**: 2026-01-25 **Category**: Research / Strategy Optimization **Source**: arXiv:2501.12397 - "Stochastic Optimal Control of Iron Condor Portfolios"

**What We Did:** - **Finding**: "Asymmetric, left-biased Iron Condor portfolios with τ = T are optimal in SPX markets" - **Meaning**: Put spread should be closer to current price than call spread - **Why**: Markets have negative skew (crashes more likely than rallies)

**The Takeaway:** - **Left-biased portfolios**: Hold to expiration (τ = T) is optimal - **Non-left-biased portfolios**: Exit at 50-75% of duration

---

## Ralph Proactive Scan Findings

**The Problem:** - Dead code detected: true

**What We Did:** Applied targeted fix based on root cause analysis

**The Takeaway:** Risk reduced and system resilience improved

---

## Ralph Proactive Scan Findings

**The Problem:** - Dead code detected: true

**What We Did:** Applied targeted fix based on root cause analysis

**The Takeaway:** Risk reduced and system resilience improved

---

## Code Changes

These commits shipped today ([view on GitHub](https://github.com/IgorGanapolsky/trading/commits/main)):

| Commit | Description |
|--------|-------------|
| [0a1a7aac](https://github.com/IgorGanapolsky/trading/commit/0a1a7aac) | docs(ralph): Auto-publish discovery blog post |
| [5852dd21](https://github.com/IgorGanapolsky/trading/commit/5852dd21) | docs(ralph): Auto-publish discovery blog post |
| [be55c434](https://github.com/IgorGanapolsky/trading/commit/be55c434) | docs(ralph): Auto-publish discovery blog post |
| [57fd31c6](https://github.com/IgorGanapolsky/trading/commit/57fd31c6) | docs(ralph): Auto-publish discovery blog post |
| [43103a21](https://github.com/IgorGanapolsky/trading/commit/43103a21) | docs(ralph): Auto-publish discovery blog post |


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
