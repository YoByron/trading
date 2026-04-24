from typing import Dict, List, Any, Optional

class AnchorBrowserProvider:
    def __init__(self):
        self.browser_config: Dict[str, Any] = {}
        self.session_active = False

    def initialize(self, config: Dict[str, Any] = None):
        if config:
            self.browser_config.update(config)
        self.session_active = True

    def navigate(self, url: str) -> bool:
        if not self.session_active:
            return False
        return True

    def execute_script(self, script: str) -> Any:
        if not self.session_active:
            return None
        return {"executed": True}

    def close(self):
        self.session_active = False

class BrowserAutomationPilot:
    def __init__(self):
        self.provider: Optional[AnchorBrowserProvider] = None
        self.automation_steps: List[Dict[str, Any]] = []

    def set_provider(self, provider: AnchorBrowserProvider):
        self.provider = provider

    def add_step(self, step: Dict[str, Any]):
        self.automation_steps.append(step)

    def execute_automation(self) -> bool:
        if not self.provider or not self.provider.session_active:
            return False
        
        for step in self.automation_steps:
            if not self._execute_step(step):
                return False
        return True

    def _execute_step(self, step: Dict[str, Any]) -> bool:
        action = step.get("action", "")
        if action == "navigate":
            return self.provider.navigate(step.get("url", ""))
        elif action == "script":
            result = self.provider.execute_script(step.get("script", ""))
            return result is not None
        return True