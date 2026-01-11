---
layout: lesson
title: "Lesson Learned #080: Dialogflow Trade Query Detection Fix"
date: 2026-01-05
category: System Integration
severity: HIGH
---

# Lesson Learned #080: Dialogflow Trade Query Detection Fix

**ID**: LL-080
**Date**: January 5, 2026
**Severity**: HIGH
**Category**: System Integration, Dialogflow, RAG

## The Incident

User asked Dialogflow: "How much money we made today?"

Dialogflow responded with lessons learned (ll_023, ll_074) about past incidents instead of actual portfolio P/L data.

## Root Cause

1. **Missing Keywords**: `is_trade_query()` function lacked common money-related words: "money", "made", "earn", "earned", "today", "balance", "account", "equity", "gains", "returns"

2. **No Fallback**: When ChromaDB had no trade history, webhook fell back to lessons RAG instead of reading current state from `system_state.json`

## The Fix (PR #1071)

1. Added 9 new trade keywords to `is_trade_query()`:
   - money, made, earn, earned, today, gains, returns, equity, balance, account

2. Added `get_current_portfolio_status()` function that reads from `system_state.json`

3. When trade query detected but no trades found → return formatted portfolio status

## Follow-up Fix (Jan 5, 2026 - v2.3.0)

The initial fix worked locally but failed in Cloud Run because:

1. **Container Has No Data**: `data/system_state.json` doesn't exist in Docker container
2. **ChromaDB Empty**: No trades with `type="trade"` in deployed database
3. **Final Fallback Wrong**: Dumped RAG lessons for P/L questions (unhelpful)

**Solution**:
- Added GitHub raw URL fallback: Fetch `system_state.json` from GitHub
- Changed final fallback to clear message instead of lessons dump

## Prevention

1. **Keyword Coverage**: Always test query detection with natural language variations
2. **Graceful Fallbacks**: Always have multiple data source fallbacks (local → GitHub → clear message)
3. **Test Deployment**: Test webhook behavior in Cloud Run, not just locally
4. **Don't Dump Unrelated Data**: If query is about X, don't return data about Y as fallback

## Keywords

dialogflow, trade query, money, portfolio, system_state, fallback, webhook
