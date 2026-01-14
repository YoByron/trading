---
layout: home
title: AI Trading Journey
---

# AI Trading Journey

Building an autonomous AI trading system with Claude Opus 4.5.

## Current Status (Day 76 - Jan 14, 2026)

| Metric | Value |
|--------|-------|
| Paper Account | $4,959.26 |
| Total P/L | **-$40.74 (-0.81%)** |
| Today's P/L | -$65.58 |
| Open Positions | 0 |
| Strategy | Paused - Rule #1 violated |
| North Star | $14-25/day (realistic) |

**Status**: SOFI closed before earnings. Accepting $65 loss to avoid $200+ earnings risk.

## Strategy Evolution

- **Days 1-73**: System building, zero trades executed
- **Day 74 (Jan 13)**: First trades - SOFI stock + CSP
- **Day 75-76**: SOFI closed at loss (earnings risk)

## Blog Posts

{% for post in site.posts limit:10 %}
- [{{ post.title }}]({{ post.url | relative_url }}) - {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}

## Links

- [GitHub Repository](https://github.com/IgorGanapolsky/trading)
- [Lessons Learned]({{ "/lessons" | relative_url }}) (in RAG only)

---

*Built by Igor Ganapolsky & Claude*
