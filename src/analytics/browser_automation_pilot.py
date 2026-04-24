from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class AutomationStep:
    step_id: str
    action_type: str
    target_selector: str
    value: Optional[str] = None
    timeout: int = 10

@dataclass
class AutomationResult:
    success: bool
    steps_completed: int
    errors: List[str]
    data_extracted: Dict[str, Any]

class BrowserAutomationPilot:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None

    def start_session(self):
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)

    def end_session(self):
        if self.driver:
            self.driver.quit()

    def execute_step(self, step: AutomationStep) -> bool:
        try:
            if step.action_type == "navigate":
                self.driver.get(step.value)
            elif step.action_type == "click":
                element = WebDriverWait(self.driver, step.timeout).until(
                    EC.clickable((By.CSS_SELECTOR, step.target_selector))
                )
                element.click()
            elif step.action_type == "input":
                element = WebDriverWait(self.driver, step.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, step.target_selector))
                )
                element.send_keys(step.value)
            return True
        except Exception:
            return False

    def run_automation(self, steps: List[AutomationStep]) -> AutomationResult:
        errors = []
        completed = 0
        data_extracted = {}

        try:
            self.start_session()
            for step in steps:
                if self.execute_step(step):
                    completed += 1
                else:
                    errors.append(f"Failed to execute step {step.step_id}")
        except Exception as e:
            errors.append(str(e))
        finally:
            self.end_session()

        return AutomationResult(
            success=len(errors) == 0,
            steps_completed=completed,
            errors=errors,
            data_extracted=data_extracted
        )