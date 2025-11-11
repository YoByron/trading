package risk

import (
	"errors"
	"math"
	"strings"

	"google.golang.org/adk/tool"
	"google.golang.org/adk/tool/functiontool"
)

type Input struct {
	Symbol         string  `json:"symbol"`
	Action         string  `json:"action"`
	Confidence     float64 `json:"confidence"`
	Volatility     float64 `json:"volatility"`
	PortfolioValue float64 `json:"portfolioValue"`
	MaxRiskBps     float64 `json:"maxRiskBps,omitempty"`
}

type Output struct {
	Decision      string  `json:"decision"`
	Reason        string  `json:"reason"`
	PositionSize  float64 `json:"positionSize"`
	ExpectedRisk  float64 `json:"expectedRisk"`
	Confidence    float64 `json:"confidence"`
	Volatility    float64 `json:"volatility"`
	ConstraintHit bool    `json:"constraintHit"`
}

func New(defaultPortfolioValue float64) (tool.Tool, error) {
	if defaultPortfolioValue <= 0 {
		return nil, errors.New("default portfolio value must be positive")
	}
	handler := func(ctx tool.Context, input Input) Output {
		portfolioValue := input.PortfolioValue
		if portfolioValue <= 0 {
			portfolioValue = defaultPortfolioValue
		}

		maxRiskBps := input.MaxRiskBps
		if maxRiskBps <= 0 {
			maxRiskBps = 50 // 0.5%
		}

		riskBudget := portfolioValue * (maxRiskBps / 10000.0)
		vol := math.Max(input.Volatility, 0.01)
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
	return functiontool.New(functiontool.Config{
		Name:        "risk_budget_check",
		Description: "Evaluate the proposed trade against volatility-adjusted risk budgets and return an approval decision.",
	}, handler)
}

func clamp(v, min, max float64) float64 {
	if v < min {
		return min
	}
	if v > max {
		return max
	}
	return v
}
