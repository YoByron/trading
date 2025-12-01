# RAG System Improvement Plan (2025)

Based on deep research into state-of-the-art financial RAG architectures, here is the roadmap to upgrade our current system from **RAG 1.0** (Basic Semantic Search) to **RAG 2.0** (Hybrid, Agentic, & Graph-Enhanced).

## 1. Immediate Upgrades (Low Effort, High Impact)

### ✅ Hybrid Search (Implemented)
**Concept**: Combine **Semantic Search** (Vector/Embedding) with **Lexical Search** (Keyword/BM25).
-   **Why**: Vectors are great for concepts ("market crash"), but BM25 is better for specific entities ("Ticker: NVDA", "PE Ratio").
-   **Implementation**:
    -   Use `rank_bm25` for keyword scoring.
    -   Use `sentence-transformers` for semantic scoring.
    -   **Reciprocal Rank Fusion (RRF)** to combine results.

### ✅ Re-Ranking (Implemented)
**Concept**: Retrieve a larger set of candidates (e.g., Top 50) and re-score them using a high-precision Cross-Encoder model.
-   **Why**: Bi-encoders (used for retrieval) are fast but less accurate. Cross-encoders are slow but highly accurate.
-   **Tool**: `sentence-transformers/cross-encoder`.
-   **Status**: Active in `InMemoryCollection`. Uses `ms-marco-MiniLM-L-6-v2`.

## 2. Strategic Enhancements (Medium Effort)

### 🕸️ GraphRAG (Knowledge Graph)
**Concept**: Instead of just chunking text, extract entities (Companies, CEOs, Products) and relationships.
-   **Structure**: `(Apple)-[COMPETES_WITH]->(Microsoft)`, `(Elon Musk)-[CEO_OF]->(Tesla)`.
-   **Benefit**: Enables multi-hop reasoning. "How will a rate hike affect tech stocks?" requires understanding the relationship between *Interest Rates* -> *Cost of Capital* -> *Growth Stocks*.
-   **Stack**: Neo4j (Graph DB) + LLM for extraction.

### 🤖 Agentic RAG
**Concept**: Agents that don't just "search" but "plan".
-   **Workflow**:
    1.  User asks: "Compare NVDA and AMD fundamentals."
    2.  Agent plans: "Fetch NVDA financials", "Fetch AMD financials", "Search recent news for both", "Synthesize".
    3.  Agent executes multiple RAG queries and aggregates.

## 3. Data Quality & Compliance

### 🏷️ Metadata-Aware Chunking
**Concept**: Don't just chunk by character count. Chunk by *financial section*.
-   **Example**: Keep "Risk Factors" separate from "Management Discussion".
-   **Implementation**: Custom parsers for 10-K/10-Q filings.

### ⏱️ Temporal Scoring
**Concept**: Financial news decays fast.
-   **Formula**: `Final_Score = Relevance_Score * Decay_Factor(Time_Elapsed)`
-   **Goal**: Prioritize fresh news for trading signals, but keep historical context for trend analysis.

---

## Current Status: RAG 1.5 (Hybrid In-Memory)
We have successfully implemented **Hybrid Search** in our `InMemoryCollection` fallback. This gives us SOTA-like retrieval quality even without a heavy Vector DB infrastructure.
