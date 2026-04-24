from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class RetroCapture:
    context: str
    analysis: str
    recommendations: List[str]

def build_context_bundle(data: Dict[str, Any]) -> Dict[str, Any]:
    """Build a context bundle from input data"""
    return {
        "timestamp": data.get("timestamp"),
        "source": data.get("source", "unknown"),
        "context": data.get("context", ""),
        "metadata": data.get("metadata", {})
    }

def generate_retro_template(retro_capture: RetroCapture) -> str:
    """Generate a retrospective template from capture data"""
    return f"""
# Retrospective Analysis

## Analysis
{retro_capture.analysis}

## Recommendations
{chr(10).join([f"- {rec}" for rec in retro_capture.recommendations])}

### Context
{retro_capture.context}
"""