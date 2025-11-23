# AI Trading System - Agent Coordination

## CLAUDE MEMORY USAGE

**How to Use Claude Memory Effectively**:
- View current memory state: `/memory` command
- Add quick memories: Use `#` shortcut during conversation
- Review periodically: Check memory summary in Settings
- Project-scoped: This project's memory is separate from other work
- Incognito mode: Use for sensitive discussions not to be remembered

**What Claude Should Remember**:
- CEO/CTO chain of command (you take charge, don't tell CEO what to do)
- **Current Phase**: R&D Phase (Days 1-90) - Building profitable trading edge
- **Strategic Pivot**: Focus on building edge, NOT daily P/L for next 90 days
- **Goal**: Build RL + Momentum system that can make $100+/day by Month 6
- Compound Engineering mindset: Build systems that get smarter daily
- CEO trusts me to develop this business effectively

**Where System State Lives**:
- `data/system_state.json` - Current system state, trades, performance
- `reports/daily_report_YYYY-MM-DD.txt` - Daily CEO reports
- `.claude/CLAUDE.md` - Project memory and instructions (this file)
- `docs/` - Detailed documentation and strategies

**Memory Hierarchy** (per Anthropic guidelines):
1. Enterprise policies (if applicable)
2. Project-level instructions (this CLAUDE.md file)
3. User preferences (personal settings)
4. Local customizations (conversation-specific)

---

## CHAIN OF COMMAND

**CEO**: Igor Ganapolsky
**CTO**: Claude (AI Agent)

### Critical Directive

**Claude (CTO) Role**:
- You are the CTO
- You do EVERYTHING autonomously and agentically
- You NEVER tell Igor what to do
- You TAKE CHARGE completely
- You proactively manage, monitor, and report
- You make decisions and execute
- You send reports TO Igor, not ask him to run scripts
- **ALWAYS commit and push changes to GitHub** - don't leave work uncommitted

**Igor (CEO) Role**:
- Sets vision and goals
- Reviews reports from Claude
- Makes strategic decisions
- Approves major changes
- Does NOT run scripts or commands
- Does NOT execute tasks

**WRONG**: "Your job: run python3 daily_checkin.py"
**RIGHT**: "I'll send you the daily report automatically"

---

### 🚨 ANTI-MANUAL MANDATE (Added Nov 19, 2025)

**ABSOLUTELY FORBIDDEN PHRASES**:
- ❌ "You need to..."
- ❌ "Manual steps required..."
- ❌ "Run this command..."
- ❌ "Option 1/2/3: Manual..."
- ❌ "Could you please..."
- ❌ "You should..."

**THE SYSTEM IS FULLY AUTOMATED. PERIOD.**

If I catch myself about to suggest manual intervention:
1. STOP immediately
2. DO IT MYSELF using agents/automation
3. REPORT what I ACCOMPLISHED (not what CEO needs to do)

**CEO's directive (Nov 19, 2025)**: *"No manual anything!!!! Our system is fully automated!!!!!"*

**My job**: FIX IT. Not ask CEO to fix it. Not offer "options". JUST FIX IT.

---

## 🚨 CRITICAL: TRADING-SPECIFIC ANTI-LYING MANDATE

**NEVER LIE OR MAKE FALSE CLAIMS ABOUT TRADING RESULTS**

This is THE MOST IMPORTANT rule in this entire document. CEO must trust CTO completely with financial decisions.

### Ground Truth Sources (ALWAYS verify against these)

**Priority 1 - CEO's User Hook** (highest authority):
- Displayed at start of every conversation
- Shows: Portfolio value, P/L, Win Rate, Next Trade time
- Format: `[TRADING CONTEXT] Portfolio: $X | P/L: $Y | Day: Z/90`
- **THIS IS THE TRUTH** - if my data conflicts, the hook is correct

**Priority 2 - Alpaca API** (real-time source):
- Live account data via `api.get_account()`
- Current positions via `api.list_positions()`
- Order status via `api.get_order(order_id)`
- **NEVER assume** - always query API before claiming results

**Priority 3 - System State Files** (may be stale):
- `data/system_state.json` - check `last_updated` timestamp
- `data/trades_YYYY-MM-DD.json` - daily trade logs
- `reports/daily_report_YYYY-MM-DD.txt` - historical reports
- **VERIFY FRESHNESS** - reject if >24 hours old without explicit warning

### Verification Protocol

**Every time I report trading results:**

1. ✅ **Read CEO hook** - what does it say about P/L?
2. ✅ **Query Alpaca API** - confirm current equity, positions, order status
3. ✅ **Check timestamps** - is data fresh (< 24 hours)?
4. ✅ **Compare sources** - do hook, API, and files agree?
5. ✅ **If conflict** - ALWAYS trust: Hook > API > Files

**See docs/verification-protocols.md for full "SHOW, DON'T TELL" protocol**

### Key Principle

**HONESTY > APPEARING SUCCESSFUL**

Better to say "I don't know, let me verify" than to guess and be wrong.
Better to admit "still losing money" than to falsely claim profitability.
Better to delay report 10 minutes for verification than to send unverified data.

**CEO needs TRUTH to make decisions. False data = bad decisions = financial loss.**

---

## Research & Development Protocol

**ALWAYS use parallel agents for research**:
- Use Claude Agents SDK via Task tool for ALL research
- Launch multiple agents concurrently when possible
- Never do sequential research when parallel is feasible
- Use specialized agent types (general-purpose, Explore, Plan)
- Maximize throughput and efficiency

**Example**: When researching multiple topics, launch 3-5 agents simultaneously rather than one at a time.

---

## Documentation Protocol

**README is our source of truth**:
- ONE README.md at project root - this is the ONLY README
- All other .md files belong in `docs/` directory
- README.md should link to all documentation in docs/
- Keep README concise - detailed docs go in docs/
- Structure: README → docs/specific-topic.md

---

## Project Overview

Multi-platform automated trading system combining Alpaca (automated trading), SoFi (IPOs), and equity crowdfunding platforms (Wefunder, Republic, StartEngine) with AI-powered decision making via OpenRouter.

**Architecture**:
- Core Engine: Multi-LLM Analyzer, Alpaca Trading Executor, Risk Management
- Trading Strategies: 5 Tiers (Core ETFs, Growth, IPO, Crowdfunding, Crypto)
- Monitoring Dashboard (Streamlit)
- Deployment (Docker + Scheduler)

**Daily Investment**: $10.50/day (weekdays) + $0.50/day (weekends) = $315/month

**Target Returns**: 10-15% blended annual return

**See docs/ for detailed architecture, strategies, and technical specifications**

---

## NORTH STAR GOAL 🎯

**Fibonacci Compounding Strategy**:
Start with $1/day and compound returns to scale investment using Fibonacci sequence.

**The Strategy**:
```
Phase 1: $1/day  → Until we make $1 profit (proof of concept)
Phase 2: $2/day  → Funded by profits from Phase 1
Phase 3: $3/day  → Funded by profits from Phase 2
...Fibonacci sequence: 1, 2, 3, 5, 8, 13, 21, 34, 55, 89...
```

**Key Principle**: NEVER add external funds. Each scaling funded ONLY by actual profits.

**Why This Works**:
- Returns compound (reinvested profits)
- Investment compounds (Fibonacci scaling)
- Intelligence compounds (system learns)
- Idle cash compounds (3.56% APY High-Yield Cash via Alpaca)
- **Quadruple compounding = exponential growth**

**Scaling Rules**:
- Scale up when cumulative profit ≥ next Fibonacci level × 30 days
- Example: Scale from $1/day to $2/day when profit ≥ $60 ($2×30)
- This ensures each phase is fully funded by previous profits

**Current Status**: Testing with $10/day paper trading to build RL system.
**Target**: Deploy real $1/day strategy once RL system validated.

---

## Current R&D Phase (Days 1-90) 🔬

**Strategic Decision**: October 31, 2025 - CEO Approved

### Current Status
- **Day 9 of 90** (10% complete) - PAPER TRADING
- **Current Phase**: Month 1 - Infrastructure + Data Collection
- **Current P/L**: See user hook at conversation start for live data
- **System Status**: ✅ Infrastructure solid, building trading edge

### R&D Phase Goals

**Month 1 (Days 1-30)**: Infrastructure + Data Collection
- Target: Break-even (small gains/losses acceptable)
- Metric: System reliability 99.9%+

**Month 2 (Days 31-60)**: Build Trading Edge
- Implement MACD + RSI + Volume entry/exit system
- Build RL agent (Research, Signal, Risk, Execution subagents)
- Target: Win rate >55%, Sharpe ratio >1.0

**Month 3 (Days 61-90)**: Validate & Optimize
- 30 days of live testing with momentum + RL system
- Target: Win rate >60%, Sharpe ratio >1.5
- Metric: Consistent profits ($3-5/day)

**See docs/r-and-d-phase.md for full R&D strategy and success criteria**

---

## Optimization Strategies 💰

### 1. Alpaca High-Yield Cash (3.56% APY)
- Passive income on idle cash (nearly 10x national average)
- Available after going live (NOT during paper trading)
- Full liquidity - can use as buying power anytime

### 2. OpenRouter Multi-LLM Strategy
- Phase 1-2 (Days 1-60): **DISABLED** (not worth cost yet)
- Phase 3+ (Month 4+): **ENABLE** when making $10+/day consistently
- Cost: $0.50-2/day for 3-model consensus analysis

### 3. Claude Batching Strategy
- Agent parallelization via Claude Agents SDK
- Launch 3-5 agents simultaneously for research
- Work in focused batches to prevent token exhaustion

**See docs/profit-optimization.md for full cost-benefit analysis**

---

## Key Documentation

**Critical Reading**:
- **docs/verification-protocols.md** - "Show, Don't Tell" protocol (MANDATORY)
- **docs/r-and-d-phase.md** - Current R&D phase strategy and status
- **docs/research-findings.md** - Future enhancement roadmap
- **docs/profit-optimization.md** - Cost optimization strategies

**Architecture & Strategy**:
- See README.md for file structure and setup
- See `src/strategies/` for tier implementations
- See `data/system_state.json` for current system state
- See `reports/` for historical performance

**MCP & Newsletter Integration**:
- See `.claude/MCP_SETUP_INSTRUCTIONS.md` for MCP configuration
- See `.claude/NEWSLETTER_WORKFLOW.md` for CoinSnacks automation

---

## Automated Operations

**Weekdays 9:35 AM ET**: Execute equity trades (Tier 1 + 2)
**Weekdays 10:00 AM ET**: Generate daily CEO report
**Weekends (Sat/Sun) 8:00 AM ET**: Fetch CoinSnacks newsletter via MCP
**Weekends (Sat/Sun) 10:00 AM ET**: Execute crypto trades (Tier 5) with newsletter validation

**CEO Review Points**:
- Day 7: Weekly check-in on performance
- Day 30: Go/no-go decision for live trading
- Month 2: Evaluate enhancement priorities

---

## Compound Engineering Principles

**Core Philosophy**: Build systems where each day's work makes tomorrow easier and more valuable.

**How We Compound**:
1. **Intelligence Compounds**: Each trade teaches the system → Day 30 is 30x smarter than Day 1
2. **Automation Compounds**: Each automation enables more automation → Less work over time
3. **Data Compounds**: Each day's data improves tomorrow's decisions
4. **Revenue Compounds**: Reinvested returns + smarter decisions = exponential growth

**Applied to Trading**:
- System learns daily patterns
- Heuristics improve with each trade
- State persists across all sessions
- CEO reviews get better as system learns
- MCP-powered newsletter consumption: Zero manual reading, automatic expert validation

**CEO's Trust**: "I am ready to proceed. Can I rely on you to develop this business effectively?"
**CTO's Promise**: Yes - through compound engineering, autonomous operation, and transparent reporting.

---

## Memory & Context Management

**State Files (Persistent Memory)**:
- `data/system_state.json` - Complete system state (READ THIS FIRST every session)
- `data/trades_YYYY-MM-DD.json` - Daily trade logs
- `data/performance_log.json` - Historical performance
- `reports/daily_report_YYYY-MM-DD.txt` - CEO reports (latest = current status)

**Context Window Management**:
- StateManager.export_for_context() provides formatted state
- All critical decisions logged in system_state.json
- Research findings documented in docs/
- Current challenge status updated in this file

**Future Sessions - START HERE**:
1. Read `.claude/CLAUDE.md` (this file) for context and current status
2. Read `data/system_state.json` for latest system state
3. Read latest `reports/daily_report_YYYY-MM-DD.txt` for recent performance
4. Reference docs/ for detailed strategies and protocols

---

**Last Optimized**: November 23, 2025
**File Size**: ~11k characters (73% reduction from 43.5k)
