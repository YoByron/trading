---
layout: post
title: "Engineering Log: LL-277: Iron Condor Optimization Researc (+2 more)"
date: 2026-01-25 18:49:15
categories: [engineering, lessons-learned, ai-trading]
tags: [condor, iron, options, open]
---

Building an autonomous AI trading system means things break. Here's what we discovered, fixed, and learned today.


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

## LL-272: PDT Protection Blocks SOFI Position Close

**The Problem:** See full details in lesson ll_272_pdt_blocks_sofi_close_jan20

**What We Did:** **Option 1**: Wait for a day trade to fall off (5 business days from oldest day trade) **Option 2**: Deposit funds to reach $25K (removes PDT restriction) **Option 3**: Accept the loss and let the option expire worthless (Feb 13, 2026) 1. **Check day trade count BEFORE opening positions** - query Alpaca API for day trade status 2. **Never open non-SPY positions** - this was the original violation 3. **Close positions on different days from opening** - avoid same-day round trips 4. **Track day tr

**The Takeaway:** Risk reduced and system resilience improved

---

## Code Changes

These commits shipped today ([view on GitHub](https://github.com/IgorGanapolsky/trading/commits/main)):

| Commit | Description |
|--------|-------------|
| [d96e6e1d](https://github.com/IgorGanapolsky/trading/commit/d96e6e1d) | docs(ralph): Auto-publish discovery blog post |
| [7fe18417](https://github.com/IgorGanapolsky/trading/commit/7fe18417) | feat(rag): Add LL-308 lesson - RAG lesson application v |
| [0a37952e](https://github.com/IgorGanapolsky/trading/commit/0a37952e) | docs(ralph): Auto-publish discovery blog post |
| [563c1d58](https://github.com/IgorGanapolsky/trading/commit/563c1d58) | feat(rag): Add LL-308 lesson - RAG lesson application v |
| [26bf8ae1](https://github.com/IgorGanapolsky/trading/commit/26bf8ae1) | docs(ralph): Auto-publish discovery blog post |


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
