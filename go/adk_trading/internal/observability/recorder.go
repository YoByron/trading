package observability

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"
)

// DecisionEvent captures the salient facts about a trade decision emitted from the ADK stack.
type DecisionEvent struct {
	Timestamp    time.Time      `json:"timestamp"`
	Symbol       string         `json:"symbol"`
	Action       string         `json:"action"`
	Confidence   float64        `json:"confidence"`
	PositionSize float64        `json:"position_size"`
	RiskDecision string         `json:"risk_decision"`
	Error        string         `json:"error,omitempty"`
	Metadata     map[string]any `json:"metadata,omitempty"`
	Raw          map[string]any `json:"raw,omitempty"`
}

// Recorder exposes health and metrics endpoints while tracking decision statistics.
type Recorder struct {
	addr       string
	server     *http.Server
	mu         sync.RWMutex
	total      uint64
	failures   uint64
	lastUpdate time.Time
	lastEvent  DecisionEvent
}

// NewRecorder initialises a Recorder bound to the provided address (e.g. ":8091").
func NewRecorder(addr string) *Recorder {
	return &Recorder{addr: addr}
}

// Start launches the HTTP server asynchronously.
func (r *Recorder) Start(ctx context.Context) {
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", r.handleHealth)
	mux.HandleFunc("/metrics", r.handleMetrics)

	r.server = &http.Server{
		Addr:              r.addr,
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
	}

	go func() {
		if err := r.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Printf("observability server error: %v\n", err)
		}
	}()

	go func() {
		<-ctx.Done()
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if r.server != nil {
			_ = r.server.Shutdown(shutdownCtx)
		}
	}()
}

// Shutdown gracefully stops the server.
func (r *Recorder) Shutdown(ctx context.Context) error {
	if r.server == nil {
		return nil
	}
	return r.server.Shutdown(ctx)
}

// Record stores a new decision event.
func (r *Recorder) Record(event DecisionEvent) {
	event.Timestamp = event.Timestamp.UTC()
	riskDecision := strings.ToUpper(event.RiskDecision)

	r.mu.Lock()
	defer r.mu.Unlock()

	r.total++
	if event.Error != "" || (riskDecision != "" && riskDecision != "APPROVE") {
		r.failures++
	}
	r.lastUpdate = time.Now().UTC()
	r.lastEvent = event
}

func (r *Recorder) handleHealth(w http.ResponseWriter, req *http.Request) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	payload := map[string]any{
		"status":        "ok",
		"total":         r.total,
		"failures":      r.failures,
		"last_update":   r.lastUpdate,
		"last_decision": r.lastEvent,
	}
	if r.total == 0 {
		payload["status"] = "cold"
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(payload); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func (r *Recorder) handleMetrics(w http.ResponseWriter, req *http.Request) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	w.Header().Set("Content-Type", "text/plain; version=0.0.4")
	fmt.Fprintf(w, "adk_decisions_total %d\n", r.total)
	fmt.Fprintf(w, "adk_decisions_failures_total %d\n", r.failures)
	if !r.lastUpdate.IsZero() {
		fmt.Fprintf(w, "adk_last_decision_timestamp %d\n", r.lastUpdate.Unix())
	}
}
