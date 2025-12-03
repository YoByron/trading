"""AWS Lambda entrypoint for the hybrid trading orchestrator."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from scripts.autonomous_trader import main as orchestrator_main

logger = logging.getLogger("lambda_handler")
logging.basicConfig(level=logging.INFO)


def lambda_handler(event, context):
    """
    AWS Lambda handler that executes the autonomous trader pipeline.

    Returns:
        dict: API Gateway compatible response payload.
    """

    try:
        orchestrator_main()
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Trading execution completed successfully"}),
        }
    except Exception as exc:  # pragma: no cover - AWS runtime only
        logger.exception("Lambda execution failed: %s", exc)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(exc)}),
        }
