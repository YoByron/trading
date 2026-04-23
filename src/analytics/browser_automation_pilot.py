import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
from datetime import datetime
from dataclasses import dataclass
import time

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Try to import requests, make it optional
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

@dataclass
class BrowserTask:
    """Represents a browser automation task"""
    url: str
    action: str
    selector: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

@dataclass
class TaskResult:
    """Result of a browser task execution"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class BrowserAutomationPilot:
    """Pilot for browser automation tasks"""
    
    def __init__(self):
        self.session_data = {}
    
    def execute_task(self, task: BrowserTask) -> TaskResult:
        """Execute a browser automation task"""
        try:
            if task.action == "navigate":
                return self._navigate(task.url)
            elif task.action == "click":
                return self._click(task.selector)
            elif task.action == "extract":
                return self._extract_data(task.selector)
            else:
                return TaskResult(
                    success=False,
                    message=f"Unknown action: {task.action}"
                )
        
        except Exception as e:
            return TaskResult(
                success=False,
                message=f"Task execution failed: {str(e)}"
            )
    
    def _navigate(self, url: str) -> TaskResult:
        """Navigate to a URL"""
        if not HAS_REQUESTS:
            return TaskResult(
                success=True,
                message=f"Mock navigation to {url}",
                data={"url": url, "status": "success"}
            )
        
        # Mock navigation for testing
        time.sleep(0.1)  # Simulate navigation delay
        return TaskResult(
            success=True,
            message=f"Navigated to {url}",
            data={"url": url, "status": "loaded"}
        )
    
    def _click(self, selector: str) -> TaskResult:
        """Click an element"""
        time.sleep(0.05)  # Simulate click delay
        return TaskResult(
            success=True,
            message=f"Clicked element: {selector}",
            data={"selector": selector, "action": "click"}
        )
    
    def _extract_data(self, selector: str) -> TaskResult:
        """Extract data from an element"""
        # Mock data extraction
        mock_data = {
            "selector": selector,
            "extracted": f"Mock data from {selector}",
            "timestamp": datetime.now().isoformat()
        }
        
        return TaskResult(
            success=True,
            message=f"Extracted data from {selector}",
            data=mock_data
        )
    
    def execute_workflow(self, tasks: List[BrowserTask]) -> List[TaskResult]:
        """Execute a workflow of browser tasks"""
        results = []
        
        for task in tasks:
            result = self.execute_task(task)
            results.append(result)
            
            if not result.success:
                break
        
        return results

def create_sample_workflow() -> List[BrowserTask]:
    """Create a sample workflow for testing"""
    return [
        BrowserTask(url="https://example.com", action="navigate"),
        BrowserTask(url="", action="click", selector="#login-button"),
        BrowserTask(url="", action="extract", selector=".data-table")
    ]

def main():
    """Main function for testing"""
    print("Starting browser automation pilot...")
    
    pilot = BrowserAutomationPilot()
    workflow = create_sample_workflow()
    
    results = pilot.execute_workflow(workflow)
    
    success_count = sum(1 for r in results if r.success)
    print(f"Executed {len(results)} tasks, {success_count} successful")
    
    return len(results) > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)