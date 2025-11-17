#!/bin/bash
#
# Automated MCP RSS Server Setup for Claude Desktop
# This script adds the RSS MCP configuration to your Claude Desktop config
#

set -euo pipefail

echo "🔧 Setting up MCP RSS Server for Claude Desktop..."
echo ""

# Detect OS and set config path
if [[ "$OSTYPE" == "darwin"* ]]; then
    CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    echo "📍 Detected macOS"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    CONFIG_PATH="$APPDATA/Claude/claude_desktop_config.json"
    echo "📍 Detected Windows"
else
    CONFIG_PATH="$HOME/.config/Claude/claude_desktop_config.json"
    echo "📍 Detected Linux"
fi

echo "📂 Config file: $CONFIG_PATH"
echo ""

# Check if config file exists
if [ ! -f "$CONFIG_PATH" ]; then
    echo "❌ Claude Desktop config not found at: $CONFIG_PATH"
    echo ""
    echo "Please install Claude Desktop first:"
    echo "  https://claude.ai/download"
    exit 1
fi

# Backup existing config
BACKUP_PATH="${CONFIG_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CONFIG_PATH" "$BACKUP_PATH"
echo "✅ Backed up existing config to:"
echo "   $BACKUP_PATH"
echo ""

# Read existing config
EXISTING_CONFIG=$(cat "$CONFIG_PATH")

# Check if mcpServers already exists
if echo "$EXISTING_CONFIG" | grep -q '"mcpServers"'; then
    echo "⚠️  mcpServers section already exists in config"
    echo ""
    echo "Please manually add this to your mcpServers section:"
    echo ""
    echo '    "rss": {'
    echo '      "command": "npx",'
    echo '      "args": ["-y", "@veithly/rss-mcp"],'
    echo '      "env": {'
    echo '        "RSS_FEEDS": "https://medium.com/feed/coinsnacks"'
    echo '      }'
    echo '    }'
    echo ""
    echo "Full instructions: .claude/MCP_SETUP_INSTRUCTIONS.md"
    exit 0
fi

# Add mcpServers section (simple case - no existing mcpServers)
# Remove closing brace, add mcpServers, add closing brace
UPDATED_CONFIG=$(echo "$EXISTING_CONFIG" | sed '$ d')

cat > "$CONFIG_PATH" << 'EOF'
${UPDATED_CONFIG},
  "mcpServers": {
    "rss": {
      "command": "npx",
      "args": ["-y", "@veithly/rss-mcp"],
      "env": {
        "RSS_FEEDS": "https://medium.com/feed/coinsnacks"
      }
    }
  }
}
EOF

# Substitute the actual config
perl -i -pe "s|\\\$\{UPDATED_CONFIG\}|$(echo "$UPDATED_CONFIG" | sed 's/[\&/]/\\&/g')|" "$CONFIG_PATH"

echo "✅ MCP RSS server configuration added successfully!"
echo ""
echo "📋 Next steps:"
echo "  1. Completely quit Claude Desktop (Cmd+Q on Mac)"
echo "  2. Restart Claude Desktop"
echo "  3. Open a new conversation"
echo "  4. Test: Ask Claude 'What are the latest CoinSnacks posts?'"
echo ""
echo "📚 Backup saved at: $BACKUP_PATH"
echo ""
echo "✨ Done! Claude can now autonomously read CoinSnacks newsletter."
