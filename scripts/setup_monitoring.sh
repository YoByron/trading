#!/bin/bash
# Setup Telegram monitoring alerts for trading system

set -e

echo "🚀 Setting up Telegram Monitoring Alerts"
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file"
    else
        echo "❌ .env.example not found. Please create .env manually."
        exit 1
    fi
fi

echo ""
echo "📱 Telegram Bot Setup Instructions:"
echo "===================================="
echo ""
echo "1. Create a Telegram bot:"
echo "   - Open Telegram and search for @BotFather"
echo "   - Send: /newbot"
echo "   - Follow prompts to create your bot"
echo "   - Copy the bot token (looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)"
echo ""
echo "2. Get your Chat ID:"
echo "   - Start a chat with your bot"
echo "   - Send any message to your bot"
echo "   - Visit: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates"
echo "   - Find 'chat':{'id':123456789} - that's your chat ID"
echo ""
echo "3. Add to .env file:"
echo "   TELEGRAM_BOT_TOKEN=your_bot_token_here"
echo "   TELEGRAM_CHAT_ID=your_chat_id_here"
echo ""
echo "4. Test the setup:"
echo "   python3 scripts/health_check.py"
echo ""
echo "✅ Setup script complete!"
echo ""
echo "💡 Next steps:"
echo "   - Add Telegram credentials to .env"
echo "   - Test with: python3 scripts/health_check.py"
echo "   - Schedule health checks: Add to GitHub Actions or cron"
echo ""

