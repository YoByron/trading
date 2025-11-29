#!/usr/bin/env python3
"""
Clean up test/demo traces from LangSmith project.

This script identifies and optionally deletes test traces (like "Sample Agent Trace")
that are not from the actual trading system.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from langsmith import Client
except ImportError:
    print("❌ langsmith not installed. Run: pip install langsmith")
    sys.exit(1)


def identify_test_traces(client: Client, project_name: str = "default", limit: int = 50):
    """Identify test/demo traces."""
    test_keywords = [
        "sample",
        "test",
        "demo",
        "beep",
        "boop",
        "document loader",
        "example",
        "tutorial",
    ]
    
    runs = list(client.list_runs(project_name=project_name, limit=limit))
    test_traces = []
    
    for run in runs:
        is_test = False
        reason = []
        
        # Check name
        if run.name:
            name_lower = run.name.lower()
            for keyword in test_keywords:
                if keyword in name_lower:
                    is_test = True
                    reason.append(f"name contains '{keyword}'")
                    break
        
        # Check inputs
        if hasattr(run, 'inputs') and run.inputs:
            inputs_str = str(run.inputs).lower()
            for keyword in test_keywords:
                if keyword in inputs_str:
                    is_test = True
                    reason.append(f"input contains '{keyword}'")
                    break
        
        # Check outputs
        if hasattr(run, 'outputs') and run.outputs:
            outputs_str = str(run.outputs).lower()
            for keyword in test_keywords:
                if keyword in outputs_str:
                    is_test = True
                    reason.append(f"output contains '{keyword}'")
                    break
        
        if is_test:
            test_traces.append({
                "run": run,
                "reasons": reason
            })
    
    return test_traces


def main():
    """Main function."""
    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        print("❌ LANGCHAIN_API_KEY not set")
        sys.exit(1)
    
    client = Client(api_key=api_key)
    
    print("🔍 Scanning for test/demo traces...")
    print("=" * 70)
    
    # Check both projects
    projects = ["default", "trading-rl-training"]
    
    for project_name in projects:
        try:
            test_traces = identify_test_traces(client, project_name=project_name)
            
            if test_traces:
                print(f"\n📋 Found {len(test_traces)} test traces in '{project_name}':")
                for i, item in enumerate(test_traces, 1):
                    run = item["run"]
                    reasons = item["reasons"]
                    print(f"\n{i}. {run.name}")
                    print(f"   ID: {run.id}")
                    print(f"   Type: {run.run_type}")
                    print(f"   Time: {run.start_time}")
                    print(f"   Reasons: {', '.join(reasons)}")
                    
                    if hasattr(run, 'inputs') and run.inputs:
                        inp = str(run.inputs)
                        if len(inp) > 100:
                            inp = inp[:100] + "..."
                        print(f"   Input: {inp}")
            else:
                print(f"\n✅ No test traces found in '{project_name}'")
                
        except Exception as e:
            print(f"\n⚠️  Error checking '{project_name}': {e}")
    
    print("\n" + "=" * 70)
    print("💡 To delete test traces:")
    print("   1. Go to LangSmith dashboard")
    print("   2. Open each test trace")
    print("   3. Use the delete/archive option")
    print("\n💡 To generate REAL trading traces:")
    print("   python scripts/rl_training_orchestrator.py --platform local --use-langsmith")
    print("   OR run your trading system - traces will appear automatically")


if __name__ == "__main__":
    main()

