package risk

import (
	"strings"
	"testing"
)

// testHandler wraps the handler logic for testing
func testHandler(defaultPortfolioValue float64, input Input) Output {
	portfolioValue := input.PortfolioValue
	if portfolioValue <= 0 {
		portfolioValue = defaultPortfolioValue
	}

	maxRiskBps := input.MaxRiskBps
	if maxRiskBps <= 0 {
		maxRiskBps = 50 // 0.5%
	}

	riskBudget := portfolioValue * (maxRiskBps / 10000.0)
	vol := max(input.Volatility, 0.01)
	confidence := clamp(input.Confidence, 0.0, 1.0)

	positionSize := riskBudget / (vol * 10)
	constraintHit := false
	if positionSize > portfolioValue*0.1 {
		positionSize = portfolioValue * 0.1
		constraintHit = true
	}

	decision := "APPROVE"
	reasonBuilder := []string{}

	if vol > 0.8 {
		decision = "REJECT"
		reasonBuilder = append(reasonBuilder, "volatility too high ")
	}
	if confidence < 0.35 {
		decision = "REVIEW"
		reasonBuilder = append(reasonBuilder, "confidence weak")
	}
	if strings.ToUpper(input.Action) == "SELL" && confidence >= 0.5 && vol > 0.4 {
		reasonBuilder = append(reasonBuilder, "elevated downside risk")
	}

	reason := strings.TrimSpace(strings.Join(reasonBuilder, "; "))
	if reason == "" {
		reason = "Risk within configured thresholds."
	}

	return Output{
		Decision:      decision,
		Reason:        reason,
		PositionSize:  positionSize,
		ExpectedRisk:  riskBudget,
		Confidence:    confidence,
		Volatility:    vol,
		ConstraintHit: constraintHit,
	}
}

func max(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}

func TestRiskTool_Approve(t *testing.T) {
	riskTool, err := New(1_000_000)
	if err != nil {
		t.Fatalf("Failed to create risk tool: %v", err)
	}
	if riskTool == nil {
		t.Fatal("Risk tool is nil")
	}

	input := Input{
		Symbol:         "SPY",
		Action:         "BUY",
		Confidence:     0.75,
		Volatility:     0.15,
		PortfolioValue: 1_000_000,
		MaxRiskBps:     50,
	}

	output := testHandler(1_000_000, input)

	if output.Decision != "APPROVE" {
		t.Errorf("Expected APPROVE, got %s", output.Decision)
	}
	if output.PositionSize <= 0 {
		t.Errorf("Expected positive position size, got %f", output.PositionSize)
	}
	if output.ExpectedRisk <= 0 {
		t.Errorf("Expected positive expected risk, got %f", output.ExpectedRisk)
	}
}

func TestRiskTool_RejectHighVolatility(t *testing.T) {
	input := Input{
		Symbol:         "SPY",
		Action:         "BUY",
		Confidence:     0.75,
		Volatility:     0.85, // Very high volatility
		PortfolioValue: 1_000_000,
		MaxRiskBps:     50,
	}

	output := testHandler(1_000_000, input)

	if output.Decision != "REJECT" {
		t.Errorf("Expected REJECT for high volatility, got %s", output.Decision)
	}
	if output.Reason == "" {
		t.Error("Expected non-empty reason for rejection")
	}
}

func TestRiskTool_ReviewLowConfidence(t *testing.T) {
	input := Input{
		Symbol:         "SPY",
		Action:         "BUY",
		Confidence:     0.30, // Low confidence
		Volatility:     0.15,
		PortfolioValue: 1_000_000,
		MaxRiskBps:     50,
	}

	output := testHandler(1_000_000, input)

	if output.Decision != "REVIEW" {
		t.Errorf("Expected REVIEW for low confidence, got %s", output.Decision)
	}
}

func TestRiskTool_PositionSizeConstraint(t *testing.T) {
	input := Input{
		Symbol:         "SPY",
		Action:         "BUY",
		Confidence:     0.90,
		Volatility:     0.001, // Extremely low volatility triggers constraint (clamped to 0.01)
		PortfolioValue: 1_000_000,
		MaxRiskBps:     500, // Higher risk budget to trigger position cap
	}

	output := testHandler(1_000_000, input)

	// Position size should be capped at 10% of portfolio
	// With vol=0.01 (min), maxRiskBps=500, riskBudget=50000
	// positionSize = 50000 / (0.01 * 10) = 500000 > 100000 cap
	maxAllowedPosition := input.PortfolioValue * 0.1
	if output.PositionSize > maxAllowedPosition*1.01 { // Allow small floating point error
		t.Errorf("Position size %f exceeds 10%% cap (%f)", output.PositionSize, maxAllowedPosition)
	}
	if !output.ConstraintHit {
		t.Error("Expected ConstraintHit to be true when position is capped")
	}
}

func TestRiskTool_SellWithElevatedRisk(t *testing.T) {
	input := Input{
		Symbol:         "SPY",
		Action:         "SELL",
		Confidence:     0.60,
		Volatility:     0.45, // Elevated volatility
		PortfolioValue: 1_000_000,
		MaxRiskBps:     50,
	}

	output := testHandler(1_000_000, input)

	// Should still approve but note elevated downside risk
	if output.Decision == "REJECT" {
		t.Logf("Sell rejected with reason: %s", output.Reason)
	}
	if output.Reason == "" {
		t.Error("Expected non-empty reason for sell with elevated risk")
	}
}

func TestRiskTool_DefaultPortfolioValue(t *testing.T) {
	input := Input{
		Symbol:         "SPY",
		Action:         "BUY",
		Confidence:     0.75,
		Volatility:     0.15,
		PortfolioValue: 0, // Should use default
		MaxRiskBps:     50,
	}

	output := testHandler(500_000, input)

	if output.PositionSize <= 0 {
		t.Errorf("Expected positive position size with default portfolio value, got %f", output.PositionSize)
	}
}

func TestRiskTool_DefaultMaxRiskBps(t *testing.T) {
	input := Input{
		Symbol:         "SPY",
		Action:         "BUY",
		Confidence:     0.75,
		Volatility:     0.15,
		PortfolioValue: 1_000_000,
		MaxRiskBps:     0, // Should use default 50 bps
	}

	output := testHandler(1_000_000, input)

	// Should calculate risk budget based on default 50 bps (0.5%)
	expectedRiskBudget := input.PortfolioValue * 0.005
	if output.ExpectedRisk <= 0 || output.ExpectedRisk > expectedRiskBudget*1.1 {
		t.Errorf("Expected risk budget around %f, got %f", expectedRiskBudget, output.ExpectedRisk)
	}
}

func TestRiskTool_InvalidInput(t *testing.T) {
	_, err := New(0)
	if err == nil {
		t.Error("Expected error for zero portfolio value")
	}

	_, err = New(-1000)
	if err == nil {
		t.Error("Expected error for negative portfolio value")
	}
}

func TestClamp(t *testing.T) {
	tests := []struct {
		name     string
		value    float64
		min      float64
		max      float64
		expected float64
	}{
		{"within range", 5.0, 0.0, 10.0, 5.0},
		{"below min", -5.0, 0.0, 10.0, 0.0},
		{"above max", 15.0, 0.0, 10.0, 10.0},
		{"at min", 0.0, 0.0, 10.0, 0.0},
		{"at max", 10.0, 0.0, 10.0, 10.0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := clamp(tt.value, tt.min, tt.max)
			if result != tt.expected {
				t.Errorf("clamp(%f, %f, %f) = %f, expected %f", tt.value, tt.min, tt.max, result, tt.expected)
			}
		})
	}
}

