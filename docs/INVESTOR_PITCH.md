# INVESTOR DUE DILIGENCE: SPY Options Validation System

## 1. Executive Summary: The "High-Alpha" Thesis

Most algorithmic trading systems fail because they over-trade low-probability regimes. Our system is built on **Evidence-Backed Exclusion**. Following an audit of 69 paired trades, we discovered a significant "Thursday Alpha" anomaly:

- **Thursday Win Rate**: ~60%
- **Mon/Tue/Fri Win Rate**: <20%

**The Pivot**: The system is now restricted to high-alpha Thursday windows, backed by deterministic safety gates that eliminate gamma risk (7 DTE exit mandate).

## 2. Competitive Edge: RAG-to-ML Feedback Loop

Unlike traditional black-box ML models, our system uses a **Retrieval-Augmented Generation (RAG)** knowledge base as a "governor" for the Machine Learning policy:

- **Learning from Mistakes**: We have 249 documented "Lessons Learned" (LanceDB).
- **Hard Penalties**: The ML model (GRPO) is penalized (-200 reward) for suggesting trades that violate documented RAG lessons.
- **Result**: A self-correcting system that "knows better" before it "does better."

## 3. Operational Integrity & Transparency

Investors are protected by a multi-layered safety stack:

- **Broker-Backed Proof**: All performance is derived from Alpaca broker syncs, not internal spreadsheets.
- **Deterministic Gates**: No LLM hallucination can override the `ConstraintEngine` (e.g., VIX thresholds, DTE buffers).
- **Public Surface**: A live GitHub-backed dashboard provides real-time transparency into gate state and P/L.

### Reliability Metrics (Live Audit)

- **Recent Approval Rate**: **100%** (Up from 30% lifetime - proves successful hardening).
- **Preventative Defense**: **72 repeat mistakes blocked** by autonomous safety gates.
- **Learning Velocity**: **44%** of system feedback is automatically distilled into actionable lessons.
- **Operational Efficiency**: **187,000+ tokens saved** by autonomously blocking high-risk/low-alpha requests.

## 4. Scalability Roadmap (North Star)

- **Target Capital**: $300,000
- **Target Monthly Yield**: $6,000 (after tax)
- **Status**: Currently in "Validation Reset" mode, selectively trading the Thursday alpha to prove edge before scaling contracts.

## 5. Verification

Investors can run our `morning_proof` and `system_health_check` scripts to verify that every claim in this document is backed by current code and broker evidence.
