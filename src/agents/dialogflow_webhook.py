#!/usr/bin/env python3
"""
Dialogflow CX Webhook Server

Connects Dialogflow to the RAG system for intelligent responses.
Runs as a FastAPI service that Dialogflow calls for intent fulfillment.
"""

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.rag.unified_rag import UnifiedRAG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dialogflow Trading Webhook")

# Initialize RAG system
rag = UnifiedRAG()
logger.info(f"RAG initialized with {rag.lessons_collection.count()} lessons")

# Auto-ingest lessons on startup if empty
if rag.lessons_collection.count() == 0:
    logger.info("RAG empty - ingesting lessons from rag_knowledge/")
    try:
        from pathlib import Path

        lessons_dir = Path("rag_knowledge/lessons_learned")
        if lessons_dir.exists():
            for lesson_file in lessons_dir.glob("ll_*.md"):
                content = lesson_file.read_text()
                lesson_id = lesson_file.stem
                rag.ingest_lesson(lesson_id, content, {"source": str(lesson_file)})
            logger.info(f"Ingested {rag.lessons_collection.count()} lessons")
    except Exception as e:
        logger.error(f"Failed to auto-ingest lessons: {e}")


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "lessons_count": rag.lessons_collection.count(),
        "service": "dialogflow-webhook",
    }


@app.post("/webhook")
async def webhook(request: Request):
    """
    Dialogflow CX webhook endpoint.

    Handles intent fulfillment requests from Dialogflow.
    """
    try:
        body = await request.json()
        logger.info(f"Received webhook request: {body.get('intentInfo', {}).get('displayName')}")

        # Extract intent and parameters
        intent_info = body.get("intentInfo", {})
        intent_name = intent_info.get("displayName", "")
        session_info = body.get("sessionInfo", {})
        parameters = session_info.get("parameters", {})

        # Route to appropriate handler
        response_text = handle_intent(intent_name, parameters, body)

        # Return Dialogflow CX response format
        return JSONResponse(
            {"fulfillmentResponse": {"messages": [{"text": {"text": [response_text]}}]}}
        )

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return JSONResponse(
            {
                "fulfillmentResponse": {
                    "messages": [
                        {
                            "text": {
                                "text": [
                                    "I encountered an error processing your request. Please try again."
                                ]
                            }
                        }
                    ]
                }
            },
            status_code=200,
        )  # Dialogflow expects 200 even for errors


def handle_intent(intent_name: str, parameters: dict, full_body: dict) -> str:
    """Route intent to appropriate handler."""

    logger.info(f"Handling intent: {intent_name}")

    if intent_name == "lessons_learned":
        return handle_lessons_learned()

    elif intent_name == "performance_metrics":
        return handle_performance_metrics()

    elif intent_name == "trade_status":
        return handle_trade_status()

    elif intent_name == "system_health":
        return handle_system_health()

    elif intent_name == "next_trade":
        return handle_next_trade()

    else:
        # Default: Try to query RAG with the user's text
        user_query = full_body.get("text", "")
        if user_query:
            return query_rag_general(user_query)
        return "I'm connected to the trading system. How can I help you?"


def handle_lessons_learned() -> str:
    """Handle lessons learned queries."""
    try:
        results = rag.query_lessons(
            "what lessons have we learned from trading mistakes and errors", n_results=5
        )

        if not results["documents"] or not results["documents"][0]:
            return "No lessons learned yet. Keep trading and learning!"

        # Format top lessons
        response = "Here are our key lessons learned:\n\n"

        for i, (doc, metadata) in enumerate(
            zip(results["documents"][0][:3], results["metadatas"][0][:3]), 1
        ):
            # Extract title from doc (first line)
            title = doc.split("\n")[0].replace("#", "").strip()[:100]
            severity = metadata.get("severity", "").upper()

            if severity:
                response += f"{i}. [{severity}] {title}\n"
            else:
                response += f"{i}. {title}\n"

        response += f"\n📊 Total lessons: {rag.lessons_collection.count()}"

        return response

    except Exception as e:
        logger.error(f"Error handling lessons_learned: {e}")
        return "I had trouble retrieving lessons learned. Please check the system logs."


def handle_performance_metrics() -> str:
    """Handle performance metrics queries."""
    try:
        # Query RAG for performance-related lessons (not currently used in response)
        _ = rag.query_lessons("trading performance metrics win rate profit sharpe", n_results=3)

        # Read actual performance from file
        import json
        from pathlib import Path

        perf_file = Path("data/performance_log.json")
        if perf_file.exists():
            perf_data = json.loads(perf_file.read_text())
            latest = perf_data[-1] if perf_data else {}

            response = "📊 Current Performance:\n\n"
            response += f"Win Rate: {latest.get('win_rate', 'N/A')}%\n"
            response += f"Sharpe Ratio: {latest.get('sharpe_ratio', 'N/A')}\n"
            response += f"Total Trades: {latest.get('total_trades', 'N/A')}\n"
            response += f"P/L: ${latest.get('total_pl', 'N/A')}\n"

            return response
        else:
            return "Performance data not available yet. Start trading to generate metrics!"

    except Exception as e:
        logger.error(f"Error handling performance_metrics: {e}")
        return "I had trouble retrieving performance metrics."


def handle_trade_status() -> str:
    """Handle trade status queries."""
    try:
        import json
        from datetime import datetime
        from pathlib import Path

        today = datetime.now().strftime("%Y-%m-%d")
        trade_file = Path(f"data/trades_{today}.json")

        if trade_file.exists():
            trades = json.loads(trade_file.read_text())
            if trades:
                response = f"📈 Today's trades ({len(trades)}):\n\n"
                for trade in trades[-3:]:  # Last 3 trades
                    symbol = trade.get("symbol", "?")
                    side = trade.get("side", "?")
                    qty = trade.get("qty", "?")
                    price = trade.get("price", "?")
                    response += f"  • {symbol}: {side} {qty} @ ${price}\n"
                return response
            else:
                return "No trades today yet."
        else:
            return "No trades today yet."

    except Exception as e:
        logger.error(f"Error handling trade_status: {e}")
        return "I had trouble checking trade status."


def handle_system_health() -> str:
    """Handle system health queries."""
    try:
        import json
        from pathlib import Path

        state_file = Path("data/system_state.json")
        if state_file.exists():
            state = json.loads(state_file.read_text())

            response = "⚙️ System Health:\n\n"
            response += f"Mode: {state.get('mode', 'unknown').title()}\n"
            response += f"Trading: {state.get('trading_enabled', False)}\n"
            response += f"RAG: {rag.lessons_collection.count()} lessons loaded\n"

            circuit_breaker = state.get("circuit_breaker", {})
            if circuit_breaker.get("active"):
                response += f"⚠️ Circuit breaker: {circuit_breaker.get('reason')}\n"
            else:
                response += "✅ All systems operational\n"

            return response
        else:
            return "System state unavailable. Check configuration."

    except Exception as e:
        logger.error(f"Error handling system_health: {e}")
        return "I had trouble checking system health."


def handle_next_trade() -> str:
    """Handle next trade time queries."""
    try:
        import json
        from pathlib import Path

        state = json.loads(Path("data/system_state.json").read_text())
        next_trade = state.get("next_trade_time", "Unknown")

        return f"⏰ Next scheduled trade: {next_trade}"

    except Exception as e:
        logger.error(f"Error handling next_trade: {e}")
        return "I couldn't determine the next trade time. Check system_state.json"


def query_rag_general(query: str) -> str:
    """General RAG query for unmatched intents."""
    try:
        results = rag.query_lessons(query, n_results=3)

        if not results["documents"] or not results["documents"][0]:
            return "I don't have specific information about that yet. Keep trading and the system will learn!"

        # Return the most relevant lesson
        top_doc = results["documents"][0][0]
        snippet = top_doc[:300]  # First 300 chars

        return f"Based on our lessons learned:\n\n{snippet}..."

    except Exception as e:
        logger.error(f"Error in general RAG query: {e}")
        return "I had trouble finding relevant information."


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Dialogflow webhook server...")
    logger.info(f"RAG system loaded with {rag.lessons_collection.count()} lessons")

    # Host binding: 0.0.0.0 required for Cloud Run/Docker deployment
    # In production, this is behind Google Cloud's IAP and load balancer
    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")  # nosec B104 # noqa: S104 - Required for Cloud Run
    port = int(os.getenv("WEBHOOK_PORT", "8080"))
    uvicorn.run(app, host=host, port=port)
