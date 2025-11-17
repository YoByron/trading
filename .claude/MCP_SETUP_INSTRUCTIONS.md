# Claude Desktop MCP Setup Instructions

## What This Does

This MCP (Model Context Protocol) server enables Claude Desktop to read RSS feeds directly, allowing you to consume crypto newsletters (like CoinSnacks) and market analysis content during conversations.

## Installation Steps

### 1. Locate Your Claude Desktop Config File

**macOS**:
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux**:
```bash
~/.config/Claude/claude_desktop_config.json
```

### 2. Copy MCP Configuration

#### Option A: Merge with Existing Config (Recommended)

If you already have a `claude_desktop_config.json` file:

1. Open your existing config file
2. Open `.claude/mcp_config.json` (in this repo)
3. Copy the `"rss"` section from `mcpServers`
4. Paste it into your existing `mcpServers` section

Example of merged config:
```json
{
  "mcpServers": {
    "your-existing-server": {
      ...
    },
    "rss": {
      "command": "npx",
      "args": ["-y", "@veithly/rss-mcp"],
      "description": "RSS feed reader for consuming crypto newsletters and market analysis",
      "env": {
        "RSS_FEEDS": "https://medium.com/feed/coinsnacks"
      }
    }
  }
}
```

#### Option B: Fresh Installation

If you DON'T have a config file yet:

1. Copy the entire `.claude/mcp_config.json` file to the location above
2. Rename it to `claude_desktop_config.json`

### 3. Restart Claude Desktop

**Important**: You MUST completely quit and restart Claude Desktop for MCP changes to take effect.

**macOS**:
- Cmd+Q to quit Claude Desktop (or right-click dock icon → Quit)
- Reopen Claude Desktop from Applications

**Windows**:
- Right-click Claude in system tray → Exit
- Reopen Claude Desktop from Start menu

**Linux**:
- Kill the Claude Desktop process
- Restart from your launcher

### 4. Verify Installation

After restarting Claude Desktop, open a new conversation and ask:

```
What MCP servers are available? Can you read RSS feeds?
```

If successful, Claude will confirm the RSS MCP server is available and list available tools.

## Testing RSS Feed Access

Once installed, you can test by asking:

```
Read the latest posts from the CoinSnacks Medium feed
```

or

```
What are the recent articles from CoinSnacks?
```

Claude will be able to fetch and summarize the RSS feed content directly.

## Adding More RSS Feeds

To add additional feeds, edit the `RSS_FEEDS` environment variable in your config:

```json
"env": {
  "RSS_FEEDS": "https://medium.com/feed/coinsnacks,https://example.com/feed.xml,https://another-feed.com/rss"
}
```

Multiple feeds should be comma-separated.

## Troubleshooting

### MCP Server Not Showing Up

1. **Check config location**: Ensure the file is in the correct directory
2. **Check JSON syntax**: Use a JSON validator (like jsonlint.com) to verify no syntax errors
3. **Check permissions**: Ensure the config file is readable
4. **Restart again**: Sometimes requires a second restart
5. **Check Claude Desktop logs**:
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`
   - Linux: `~/.config/Claude/logs/`

### npx Command Fails

Ensure Node.js is installed:
```bash
node --version
npm --version
```

If not installed, download from: https://nodejs.org/

### RSS Feed Not Loading

- Check the feed URL is valid (test in browser)
- Ensure Medium feed is accessible (not behind paywall)
- Try running manually: `npx -y @veithly/rss-mcp`

## Package Information

**MCP Package**: `@veithly/rss-mcp`
**Repository**: https://github.com/veithly/rss-mcp
**License**: MIT

## Security Notes

- MCP servers run locally on your machine
- RSS feeds are fetched directly from the source
- No data is sent to third parties (beyond Claude's normal API usage)
- All feed data is processed within Claude Desktop context

## Benefits for Trading System

Once configured, you can:

1. **Daily Newsletter Digest**: Ask Claude to summarize today's CoinSnacks newsletter
2. **Market Sentiment Analysis**: Extract key themes and sentiment from recent posts
3. **Integration with Research**: Use newsletter insights during trading research phase
4. **Automated Monitoring**: Schedule daily checks of new content (via Claude conversations)

## Next Steps

After installation, consider:

1. Adding more crypto/finance RSS feeds (Decrypt, CoinDesk, The Block, etc.)
2. Creating a daily routine to review newsletters with Claude
3. Integrating newsletter insights into your trading research workflow
4. Building a custom skill to automate newsletter summarization

## Support

If you encounter issues:

1. Check Claude Desktop documentation: https://docs.anthropic.com/
2. Check MCP specification: https://spec.modelcontextprotocol.io/
3. Review `@veithly/rss-mcp` package issues: https://github.com/veithly/rss-mcp/issues
4. Ask Claude for help troubleshooting in a conversation
