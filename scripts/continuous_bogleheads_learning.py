#!/usr/bin/env python3
"""
Continuous Bogleheads Forum Learning

Runs continuously to monitor Bogleheads forum, extract insights,
and update RAG storage for RL engine integration.
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude.skills.bogleheads_learner.scripts.bogleheads_learner import (
    BogleheadsLearner,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Continuous learning loop"""
    learner = BogleheadsLearner()

    logger.info("🔍 Starting continuous Bogleheads forum learning...")
    logger.info("   Monitoring: Personal Investments, Investing Theory")
    logger.info("   Keywords: market timing, risk, volatility, rebalancing")

    iteration = 0

    while True:
        try:
            iteration += 1
            logger.info(f"\n{'='*80}")
            logger.info(f"Iteration {iteration} - {datetime.now().isoformat()}")
            logger.info("=" * 80)

            # Monitor forum
            result = learner.monitor_bogleheads_forum(
                topics=["Personal Investments", "Investing - Theory, News & General"],
                keywords=[
                    "market timing",
                    "rebalancing",
                    "risk",
                    "volatility",
                    "bear market",
                    "bull market",
                    "diversification",
                    "allocation",
                    "index funds",
                    "ETF",
                    "SPY",
                    "QQQ",
                    "VOO",
                ],
                max_posts=50,
                min_replies=5,
            )

            logger.info(f"📊 Monitoring result: {result}")

            # Extract insights (if posts found)
            if result.get("posts_analyzed", 0) > 0:
                logger.info("💡 Extracting insights from posts...")
                # In production, would extract insights here
                # For now, placeholder

            # Store insights to RAG
            # (Would store extracted insights here)

            # Wait before next iteration (24 hours)
            wait_hours = 24
            wait_seconds = wait_hours * 3600
            logger.info(f"⏳ Waiting {wait_hours} hours until next monitoring cycle...")
            logger.info(
                f"   Next run: {datetime.fromtimestamp(time.time() + wait_seconds).isoformat()}"
            )

            time.sleep(wait_seconds)

        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping continuous learning (KeyboardInterrupt)")
            break
        except Exception as e:
            logger.error(f"❌ Error in learning loop: {e}", exc_info=True)
            logger.info("⏳ Waiting 1 hour before retry...")
            time.sleep(3600)


if __name__ == "__main__":
    main()
