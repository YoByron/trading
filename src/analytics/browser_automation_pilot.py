from typing import Dict, List, Optional, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AnchorBrowserProvider:
    """Provides browser automation capabilities with anchor-based navigation."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        
    def start_browser(self):
        """Start the browser instance."""
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def stop_browser(self):
        """Stop the browser instance."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None
            
    def navigate_to_url(self, url: str):
        """Navigate to a specific URL."""
        if not self.driver:
            self.start_browser()
        self.driver.get(url)
        
    def find_anchor_by_text(self, text: str) -> Optional[Any]:
        """Find an anchor element by its text content."""
        if not self.driver:
            return None
            
        try:
            return self.wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, text))
            )
        except:
            return None
            
    def find_anchor_by_partial_text(self, text: str) -> Optional[Any]:
        """Find an anchor element by partial text content."""
        if not self.driver:
            return None
            
        try:
            return self.wait.until(
                EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, text))
            )
        except:
            return None
            
    def click_anchor(self, anchor_element) -> bool:
        """Click on an anchor element."""
        try:
            anchor_element.click()
            return True
        except:
            return False
            
    def get_page_title(self) -> str:
        """Get the current page title."""
        if not self.driver:
            return ""
        return self.driver.title
        
    def get_current_url(self) -> str:
        """Get the current URL."""
        if not self.driver:
            return ""
        return self.driver.current_url

class BrowserAutomationPilot:
    """Main pilot class for browser automation tasks."""
    
    def __init__(self):
        self.provider = AnchorBrowserProvider()
        self.actions_log: List[Dict[str, Any]] = []
        
    def log_action(self, action: str, details: Dict[str, Any]):
        """Log an automation action."""
        self.actions_log.append({
            'action': action,
            'details': details,
            'timestamp': str(datetime.now())
        })
        
    def navigate_and_click_anchor(self, url: str, anchor_text: str) -> bool:
        """Navigate to URL and click on anchor with specified text."""
        try:
            self.provider.navigate_to_url(url)
            anchor = self.provider.find_anchor_by_text(anchor_text)
            
            if anchor:
                success = self.provider.click_anchor(anchor)
                self.log_action('click_anchor', {
                    'url': url,
                    'anchor_text': anchor_text,
                    'success': success
                })
                return success
            else:
                self.log_action('anchor_not_found', {
                    'url': url,
                    'anchor_text': anchor_text
                })
                return False
        except Exception as e:
            self.log_action('navigation_error', {
                'url': url,
                'anchor_text': anchor_text,
                'error': str(e)
            })
            return False
            
    def cleanup(self):
        """Clean up resources."""
        self.provider.stop_browser()

from datetime import datetime