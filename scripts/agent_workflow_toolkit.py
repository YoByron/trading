#!/usr/bin/env python3
"""Agent workflow toolkit for managing multi-step processes."""

import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WorkflowContext:
    """Context for workflow execution."""
    session_id: str
    current_step: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]


def build_context_bundle(session_id: str, step_name: str, data: Dict[str, Any] = None) -> WorkflowContext:
    """Build a context bundle for workflow execution.
    
    Args:
        session_id: Unique identifier for the workflow session
        step_name: Name of the current workflow step
        data: Data payload for the step
        
    Returns:
        WorkflowContext object
    """
    if data is None:
        data = {}
        
    return WorkflowContext(
        session_id=session_id,
        current_step=step_name,
        data=data,
        metadata={
            "created_at": datetime.now().isoformat(),
            "version": "1.0"
        }
    )


def save_context(context: WorkflowContext, file_path: str = None) -> str:
    """Save workflow context to file.
    
    Args:
        context: WorkflowContext to save
        file_path: Optional file path, defaults to session-based name
        
    Returns:
        Path to saved file
    """
    if file_path is None:
        file_path = f"workflow_{context.session_id}.json"
    
    context_dict = {
        "session_id": context.session_id,
        "current_step": context.current_step,
        "data": context.data,
        "metadata": context.metadata
    }
    
    with open(file_path, 'w') as f:
        json.dump(context_dict, f, indent=2)
    
    return file_path


def load_context(file_path: str) -> WorkflowContext:
    """Load workflow context from file.
    
    Args:
        file_path: Path to context file
        
    Returns:
        WorkflowContext object
    """
    with open(file_path, 'r') as f:
        context_dict = json.load(f)
    
    return WorkflowContext(
        session_id=context_dict["session_id"],
        current_step=context_dict["current_step"],
        data=context_dict["data"],
        metadata=context_dict["metadata"]
    )


def execute_workflow_step(context: WorkflowContext, step_function: callable) -> WorkflowContext:
    """Execute a workflow step and update context.
    
    Args:
        context: Current workflow context
        step_function: Function to execute for this step
        
    Returns:
        Updated WorkflowContext
    """
    try:
        result = step_function(context.data)
        context.data.update(result)
        context.metadata["last_updated"] = datetime.now().isoformat()
        return context
    except Exception as e:
        context.metadata["error"] = str(e)
        context.metadata["error_step"] = context.current_step
        return context


if __name__ == "__main__":
    # Example usage
    context = build_context_bundle("test-session", "init", {"message": "Hello World"})
    print(f"Created context for session: {context.session_id}")