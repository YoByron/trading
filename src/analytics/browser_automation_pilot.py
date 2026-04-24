from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
import time


@dataclass
class BrowserAction:
    action_type: str
    target: str
    value: Optional[str] = None


@dataclass
class AnchorBrowserProvider:
    browser_type: str
    headless: bool = True
    
    def __post_init__(self):
        self.driver = None
    
    def start_browser(self) -> None:
        """Start the browser instance."""
        if self.browser_type == "chrome":
            options = webdriver.ChromeOptions()
            if self.headless:
                options.add_argument("--headless")
            self.driver = webdriver.Chrome(options=options)
        else:
            raise ValueError(f"Unsupported browser type: {self.browser_type}")
    
    def stop_browser(self) -> None:
        """Stop the browser instance."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def execute_action(self, action: BrowserAction) -> Dict[str, Any]:
        """Execute a browser action."""
        if not self.driver:
            return {"status": "error", "message": "Browser not started"}
        
        try:
            if action.action_type == "navigate":
                self.driver.get(action.target)
            elif action.action_type == "click":
                element = self.driver.find_element(By.CSS_SELECTOR, action.target)
                element.click()
            elif action.action_type == "type":
                element = self.driver.find_element(By.CSS_SELECTOR, action.target)
                element.send_keys(action.value)
            
            return {"status": "success", "action": action.action_type}
        except Exception as e:
            return {"status": "error", "message": str(e)}


def create_browser_provider(browser_type: str = "chrome", headless: bool = True) -> AnchorBrowserProvider:
    """Create a new browser provider instance."""
    return AnchorBrowserProvider(browser_type=browser_type, headless=headless)


def execute_automation_sequence(provider: AnchorBrowserProvider, actions: List[BrowserAction]) -> List[Dict[str, Any]]:
    """Execute a sequence of browser automation actions."""
    results = []
    provider.start_browser()
    
    try:
        for action in actions:
            result = provider.execute_action(action)
            results.append(result)
            time.sleep(1)  # Brief pause between actions
    finally:
        provider.stop_browser()
    
    return results