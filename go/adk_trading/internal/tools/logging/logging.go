package logging

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"sync"
	"time"

	"google.golang.org/adk/tool"
	"google.golang.org/adk/tool/functiontool"
)

type Input struct {
	Symbol     string         `json:"symbol"`
	Action     string         `json:"action"`
	Confidence float64        `json:"confidence"`
	Notes      string         `json:"notes,omitempty"`
	Metadata   map[string]any `json:"metadata,omitempty"`
}

type Output struct {
	Status    string    `json:"status"`
	Path      string    `json:"path"`
	Timestamp time.Time `json:"timestamp"`
}

var fileMu sync.Mutex

func New(logPath string) (tool.Tool, error) {
	if logPath == "" {
		return nil, errors.New("log path is required")
	}
	handler := func(ctx tool.Context, input Input) Output {
		timestamp := time.Now().UTC()
		entry := map[string]any{
			"timestamp":  timestamp.Format(time.RFC3339Nano),
			"symbol":     input.Symbol,
			"action":     input.Action,
			"confidence": input.Confidence,
			"notes":      input.Notes,
			"metadata":   input.Metadata,
			"agent":      ctx.AgentName(),
			"invocation": ctx.InvocationID(),
		}
		ensureDir(logPath)
		fileMu.Lock()
		defer fileMu.Unlock()
		f, err := os.OpenFile(logPath, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
		if err != nil {
			return Output{Status: "error", Path: logPath, Timestamp: timestamp}
		}
		defer f.Close()
		data, err := json.Marshal(entry)
		if err != nil {
			return Output{Status: "error", Path: logPath, Timestamp: timestamp}
		}
		if _, err := f.Write(append(data, '\n')); err != nil {
			return Output{Status: "error", Path: logPath, Timestamp: timestamp}
		}
		return Output{
			Status:    "logged",
			Path:      logPath,
			Timestamp: timestamp,
		}
	}
	return functiontool.New(functiontool.Config{
		Name:        "log_trade_decision",
		Description: "Append the proposed trade decision into the orchestrator JSONL audit log.",
	}, handler)
}

func ensureDir(path string) {
	dir := filepath.Dir(path)
	if dir == "" || dir == "." {
		return
	}
	_ = os.MkdirAll(dir, 0o755)
}
