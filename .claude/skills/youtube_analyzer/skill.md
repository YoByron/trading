# YouTube Analyzer Skill

Extracts and analyzes YouTube videos (podcasts, trading analysis, market commentary) for actionable trading insights using AI-powered transcript analysis.

## Purpose

Analyze financial content from YouTube videos to extract:
- Trading signals and stock picks
- Market sentiment and analysis
- Risk factors and warnings
- Actionable trading recommendations
- Key timestamps for important insights

## Usage

When the user provides YouTube URL(s):

1. **Extract video metadata** using yt-dlp
2. **Fetch transcript** using youtube-transcript-api
3. **Analyze content** for trading insights using AI
4. **Generate actionable recommendations** with tickers and confidence scores
5. **Save analysis** to docs/youtube_analysis/ for reference

## Supported Content Types

- Trading strategy videos
- Market analysis and commentary
- Stock picking discussions
- Economic news analysis
- Company earnings reviews
- Investment podcasts
- Financial education content

## Output Format

The skill generates comprehensive markdown reports with:

- **Executive Summary**: Key takeaways in 3-5 bullet points
- **Stock Picks**: Tickers with bullish/bearish sentiment
- **Trading Strategies**: Specific approaches mentioned
- **Risk Factors**: Warnings and cautions
- **Actionable Recommendations**: What to do next
- **Key Timestamps**: Jump to important sections
- **Full Transcript**: Complete text for reference

## Integration with Trading System

Analysis results can be:
- Fed into Multi-LLM Analyzer for sentiment scoring
- Used to inform Tier 2 Growth Strategy stock selection
- Tracked over time for accuracy validation
- Compared with actual market performance

## Requirements

This skill requires two Python packages installed in the virtual environment:

```bash
pip install yt-dlp youtube-transcript-api
```

## Command Examples

```bash
# Analyze single video
python3 analyze_youtube.py --url "https://youtube.com/watch?v=VIDEO_ID"

# Analyze with custom output directory
python3 analyze_youtube.py --url "URL" --output docs/youtube_analysis/

# Analyze video by ID only
python3 analyze_youtube.py --video-id "VIDEO_ID"

# Include AI analysis (requires OpenRouter API)
python3 analyze_youtube.py --url "URL" --analyze
```

## Skill Files

- **skill.md**: This file - skill documentation
- **README.md**: Detailed usage guide and examples
- **analyze_youtube.py**: Python script for video analysis
- **example.sh**: Example shell script demonstrating usage

## Safety & Ethics

- Only analyze public YouTube videos
- Respect content creator rights
- Use insights for educational purposes
- Verify information before trading
- Never blindly follow trading advice from videos

## Future Enhancements

- Automatic daily analysis of top financial channels
- Sentiment trend tracking across multiple videos
- Integration with Alpaca trading alerts
- AI-powered timestamp generation for key insights
- Multi-language transcript support
