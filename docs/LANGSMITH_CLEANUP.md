# LangSmith Cleanup Guide

## The "BEEP BOOP" Problem

If you see a trace called **"Sample Agent Trace"** with output like **"BEEP BOOP!"** about document loaders, this is **NOT from your trading system**. It's a LangSmith demo/test trace.

## What Happened

LangSmith automatically creates example traces when you first set up a project. These are tutorial/demo traces, not real trading data.

## How to Clean Up

### Option 1: Delete in LangSmith UI (Recommended)

1. Go to your LangSmith project: https://smith.langchain.com/o/bb00a62e-c62a-4c42-9031-43e1f74bb5b3/projects/p/04fa554e-f155-4039-bb7f-e866f082103b
2. Find the "Sample Agent Trace"
3. Click on it
4. Use the delete/archive option (usually in the top right)
5. Confirm deletion

### Option 2: Use Cleanup Script

```bash
python scripts/clean_langsmith_test_traces.py
```

This will identify all test traces (but won't delete them - you need to do that manually in the UI).

## What REAL Trading Traces Look Like

When your trading system runs, you'll see traces like:

- **Name**: `RL Training: Q-Learning` or `MultiLLMAnalyzer` or `ResearchAgent`
- **Input**: Trading symbols, market data, sentiment queries
- **Output**: Trading decisions, RL training metrics, analysis results
- **Type**: `chain`, `llm`, or `tool`

## How to Generate Real Traces

### 1. Run RL Training with LangSmith

```bash
python scripts/rl_training_orchestrator.py \
  --platform local \
  --agents q_learning \
  --use-langsmith
```

### 2. Run Trading System

Your trading system automatically sends traces when:
- MultiLLMAnalyzer analyzes sentiment
- Agents make decisions
- RL models train
- News sentiment is analyzed

Just run your normal trading workflows - traces appear automatically!

## Verifying Real Traces

After running trading/RL training, check LangSmith:

1. Go to your project
2. Look for traces with names like:
   - `RL Training: Q-Learning`
   - `MultiLLMAnalyzer`
   - `ResearchAgent`
   - `SignalAgent`
   - `MetaAgent`
3. These should have trading-related inputs/outputs

## Project Name Note

The project may show as **"default"** in the LangSmith UI, but the project ID (`04fa554e-f155-4039-bb7f-e866f082103b`) is correct. This is a LangSmith quirk - the project name can't be changed after creation, but all your traces are going to the right place.
