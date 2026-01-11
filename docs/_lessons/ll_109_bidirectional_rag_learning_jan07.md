---
layout: lesson
title: "Lesson Learned #109: Bidirectional Vertex AI RAG Learning System"
date: 2026-01-07
category: RAG
severity: HIGH
---

# Lesson Learned #109: Bidirectional Vertex AI RAG Learning System

**ID**: LL-109
**Date**: January 7, 2026
**Severity**: HIGH
**Category**: RAG, Architecture, Learning

## The Issue

We were only WRITING to Vertex AI RAG (post-trade sync), but NEVER READING from it before trades. This violated the CEO directive: "We are supposed to be LEARNING from Vertex AI RAG!"

### Evidence

```
Previous Architecture (One-Way):
┌─────────────┐    WRITE    ┌─────────────┐
│   Trading   │ ──────────► │  Vertex AI  │
│   System    │             │     RAG     │
└─────────────┘             └─────────────┘
       ▲                           │
       │    NO READ CONNECTION!    │
       └───────────────────────────┘
```

### Root Cause

1. `sync_trades_to_rag.py` only synced AFTER trades
2. No pre-trade RAG query existed
3. Sandbox SSL blocked direct Vertex AI access
4. We assumed local TF-IDF search was "RAG learning" - it wasn't using cloud data

## The Solution

Created a **bidirectional learning system** with pre-trade RAG queries via CI:

```
New Architecture (Bidirectional):
┌─────────────┐    READ     ┌─────────────┐
│  Pre-Trade  │ ◄────────── │  Vertex AI  │
│   Check     │             │     RAG     │
└─────────────┘             └─────────────┘
       │                           ▲
       ▼                           │
┌─────────────┐    WRITE    ┌─────────────┐
│   Trading   │ ──────────► │  Post-Trade │
│   Execution │             │    Sync     │
└─────────────┘             └─────────────┘
```

## Implementation Details

### New Files Created

1. **`scripts/query_vertex_rag.py`** - Queries Vertex AI RAG before trading
2. **`.github/workflows/vertex-rag-pretrade.yml`** - Standalone workflow for RAG queries
3. **Updated `daily-trading.yml`** - Added `pretrade-rag-query` job

### 2026 Best Practices Applied

1. **Gemini 2.0 Flash** - Now GA for grounded answer generation
2. **Hybrid Search** - Semantic + keyword search with re-ranking
3. **Check Grounding API** - Validates responses against facts
4. **Query-First Decision Making** - Retrieve before generating

## Impact

- **Before**: Same mistakes repeated because lessons weren't consulted
- **After**: True bidirectional learning - read lessons before trading, write lessons after
