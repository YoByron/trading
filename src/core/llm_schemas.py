from pydantic import BaseModel, Field


class SentimentResponse(BaseModel):
    """Basic sentiment analysis response."""

    sentiment: float = Field(
        ..., description="Sentiment score between -1.0 (bearish) and 1.0 (bullish)", ge=-1.0, le=1.0
    )
    reasoning: str = Field(..., description="Concise explanation for the sentiment score")


class EnhancedSentimentResponse(SentimentResponse):
    """Detailed sentiment analysis with risk factors."""

    confidence: float = Field(
        ..., description="Confidence in the analysis between 0.0 and 1.0", ge=0.0, le=1.0
    )
    key_factors: list[str] = Field(
        default_factory=list, description="List of key factors influencing the score"
    )
    risks: list[str] = Field(default_factory=list, description="List of potential risks identified")


class TradeSignal(BaseModel):
    """Trading signal extraction."""

    action: str = Field(..., description="Recommended action: BUY, SELL, or HOLD")
    confidence: float = Field(..., description="Confidence score 0.0-1.0")
    reasoning: str = Field(..., description="Justification for the signal")
    timeframe: str = Field(..., description="Relevant timeframe for the signal (e.g., '1d', '1w')")


class IPOScoreResponse(BaseModel):
    """IPO evaluation score."""

    ipo_score: int = Field(..., description="IPO attractiveness score 0-100", ge=0, le=100)
    reasoning: str = Field(..., description="Explanation for the score")
    risk_level: str = Field(..., description="Risk assessment: Low, Medium, High")
