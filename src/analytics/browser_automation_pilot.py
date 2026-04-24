from typing import Dict, Any, List
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@dataclass
class BrowserPilotRunResult:
    success: bool
    message: str
    data: Dict[str, Any] = None
    screenshots: List[str] = None

class BrowserAutomationPilot:
    def __init__(self):
        self.driver = None
    
    def initialize_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
    
    def run_automation(self, script: Dict[str, Any]) -> BrowserPilotRunResult:
        try:
            if not self.driver:
                self.initialize_driver()
            
            if "url" in script:
                self.driver.get(script["url"])
            
            return BrowserPilotRunResult(
                success=True,
                message="Automation completed successfully",
                data={"title": self.driver.title if self.driver else ""}
            )
        except Exception as e:
            return BrowserPilotRunResult(
                success=False,
                message=f"Automation failed: {str(e)}"
            )
    
    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None