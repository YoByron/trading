---
layout: post
title: "Engineering Log: LL-298: Invalid Option Strikes Causing C (+2 more)"
date: 2026-01-25 04:36:38
categories: [engineering, lessons-learned, ai-trading]
tags: [history, security, issues, detected]
---

Building an autonomous AI trading system means things break. Here's what we discovered, fixed, and learned today.


## LL-298: Invalid Option Strikes Causing CALL Legs to Fail

**The Problem:** See full details in lesson ll_298_invalid_strikes_call_legs_fail_jan23

**What We Did:** - Added `round_to_5()` function to `calculate_strikes()` - All strikes now rounded to nearest $5 multiple - Commit: `8b3e411` (PR pending merge) 1. Always round SPY strikes to $5 increments 2. Verify ALL 4 legs fill before considering trade complete 3. Add validation that option symbols exist before submitting orders 4. Log when any leg fails to fill - LL-297: Incomplete iron condor crisis (PUT-only positions) - LL-281: CALL leg pricing fallback iron_condor, options, strikes, call_legs, validati

**The Takeaway:** Risk reduced and system resilience improved

---

## ---

**The Problem:** id: LL-298 title: $22.61 Loss from SPY Share Churning - Crisis Workflow Failure date: 2026-01-23

**What We Did:** severity: CRITICAL category: trading Lost $22.61 on January 23, 2026 from 49 SPY share trades instead of iron condor execution.

**The Takeaway:** 1. Crisis workflows traded SPY SHARES (not options) 2. Iron condor failed due to:

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
| [9ddcbe07](https://github.com/IgorGanapolsky/trading/commit/9ddcbe07) | chore(ralph): CI iteration ✅ |
| [fc571971](https://github.com/IgorGanapolsky/trading/commit/fc571971) | docs(ralph): Auto-publish discovery blog post |
| [0b4042d3](https://github.com/IgorGanapolsky/trading/commit/0b4042d3) | docs(blog): Ralph discovery - docs(ralph): Auto-publish |
| [32587214](https://github.com/IgorGanapolsky/trading/commit/32587214) | docs(ralph): Auto-publish discovery blog post |
| [f64bbd14](https://github.com/IgorGanapolsky/trading/commit/f64bbd14) | chore(ralph): Record proactive scan findings |


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
