#!/usr/bin/env python3
"""
Gemini 3 Trading Analysis

Demonstrates Gemini 3 multi-agent system for trading analysis.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.gemini3_integration import get_gemini3_integration


def main():
    """Run Gemini 3 trading analysis."""
    print("=" * 80)
    print("🧠 GEMINI 3 TRADING ANALYSIS")
    print("=" * 80)
    
    # Get integration
    integration = get_gemini3_integration()
    
    if not integration.enabled:
        print("\n❌ Gemini 3 not available")
        print("   Set GOOGLE_API_KEY environment variable to enable")
        return
    
    print("\n✅ Gemini 3 integration enabled")
    
    # Example market data
    market_data = {
        "symbols": ["SPY", "QQQ", "VOO"],
        "timestamp": "2025-11-20T16:00:00",
        "market_regime": "neutral",
        "volatility": "moderate",
    }
    
    print("\n📊 Analyzing market with Gemini 3...")
    print(f"   Thinking level: medium")
    print(f"   Symbols: {market_data['symbols']}")
    
    # Analyze with medium thinking level
    result = integration.analyze_market(
        symbols=market_data["symbols"],
        market_data=market_data,
        thinking_level="medium",
    )
    
    if "error" in result:
        print(f"\n❌ Error: {result['error']}")
        return
    
    print("\n" + "=" * 80)
    print("📋 ANALYSIS RESULTS")
    print("=" * 80)
    
    if result.get("decision"):
        decision = result["decision"]
        print(f"\n🎯 Decision: {decision.get('action', 'N/A')}")
        print(f"   Symbol: {decision.get('symbol', 'N/A')}")
        print(f"   Confidence: {decision.get('confidence', 0):.2f}")
        print(f"   Reasoning: {decision.get('reasoning', 'N/A')}")
    
    if result.get("analysis"):
        analysis = result["analysis"]
        print(f"\n📊 Analysis:")
        if "research" in analysis:
            print(f"   Research: {analysis['research'][:200]}...")
        if "technical" in analysis:
            print(f"   Technical: {analysis['technical'][:200]}...")
    
    if result.get("thought_signatures"):
        print(f"\n🧠 Thought Signatures: {len(result['thought_signatures'])} preserved")
    
    print("\n" + "=" * 80)
    print("✅ Analysis Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()

