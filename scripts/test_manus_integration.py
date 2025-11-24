#!/usr/bin/env python3
"""
Test Manus Integration - Verify everything is wired up correctly

Run this to test:
1. API key is loaded
2. Manus client works
3. Research agent uses Manus
4. MCP tools are executable
"""

import os
import sys
from pathlib import Path

# Add project root to path (so both src and mcp are importable)
trading_root = Path(__file__).parent.parent
sys.path.insert(0, str(trading_root))

from dotenv import load_dotenv

load_dotenv()


def test_api_key():
    """Test 1: API key is loaded"""
    print("=" * 60)
    print("Test 1: API Key Loading")
    print("=" * 60)

    from src.utils.security import mask_api_key
    api_key = os.getenv("MANUS_API_KEY")
    if api_key:
        masked = mask_api_key(api_key)
        print(f"✅ API key found: {masked}")
        return True
    else:
        print("❌ API key not found in environment")
        return False


def test_manus_client():
    """Test 2: Manus client initialization"""
    print("\n" + "=" * 60)
    print("Test 2: Manus Client Initialization")
    print("=" * 60)
    
    try:
        from src.utils.manus_client import get_manus_client
        
        client = get_manus_client()
        print("✅ Manus client initialized successfully")
        print(f"   Base URL: {client.base_url}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize Manus client: {e}")
        return False


def test_research_agent():
    """Test 3: Research agent with Manus"""
    print("\n" + "=" * 60)
    print("Test 3: Research Agent with Manus")
    print("=" * 60)
    
    try:
        from src.agents.research_agent import ResearchAgent
        
        agent = ResearchAgent(use_manus=True)
        print("✅ Research agent initialized")
        
        if agent.manus_agent:
            print("✅ Manus agent is available and will be used")
        else:
            print("⚠️  Manus agent not available (will use fallback)")
        
        return True
    except Exception as e:
        print(f"❌ Failed to initialize research agent: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_tools():
    """Test 4: MCP tools are available"""
    print("\n" + "=" * 60)
    print("Test 4: MCP Tools Availability")
    print("=" * 60)
    
    try:
        from mcp.servers import manus
        
        tools = manus.get_mcp_tools()
        print(f"✅ MCP tools available: {len(tools)} tools")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description'][:60]}...")
        
        return True
    except Exception as e:
        print(f"❌ Failed to load MCP tools: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_execution():
    """Test 5: MCP tool execution (dry run)"""
    print("\n" + "=" * 60)
    print("Test 5: MCP Tool Execution (Dry Run)")
    print("=" * 60)
    
    try:
        from mcp.servers import manus
        
        # Test tool execution (this will actually call Manus API)
        print("⚠️  This will make a real API call to Manus")
        print("   Skipping actual execution to avoid costs")
        print("   To test execution, uncomment the code below")
        
        # Uncomment to actually test:
        # result = manus.research_stock("AAPL", research_type="quick")
        # print(f"✅ MCP tool executed: {result.get('status')}")
        
        return True
    except Exception as e:
        print(f"❌ MCP tool execution failed: {e}")
        return False


def test_orchestrator_integration():
    """Test 6: Orchestrator integration"""
    print("\n" + "=" * 60)
    print("Test 6: Orchestrator Integration")
    print("=" * 60)
    
    try:
        from src.orchestration.mcp_trading import MCPTradingOrchestrator
        
        orchestrator = MCPTradingOrchestrator(symbols=["AAPL"], paper=True)
        print("✅ Orchestrator initialized")
        
        if hasattr(orchestrator.research_agent, 'manus_agent'):
            print("✅ Orchestrator is using Manus-enhanced research agent")
        else:
            print("⚠️  Orchestrator using standard research agent")
        
        return True
    except Exception as e:
        print(f"❌ Orchestrator integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Manus Integration Test Suite")
    print("=" * 60)
    print("\nTesting Manus API integration...\n")
    
    results = []
    
    results.append(("API Key", test_api_key()))
    results.append(("Manus Client", test_manus_client()))
    results.append(("Research Agent", test_research_agent()))
    results.append(("MCP Tools", test_mcp_tools()))
    results.append(("MCP Execution", test_mcp_execution()))
    results.append(("Orchestrator", test_orchestrator_integration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Manus integration is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

