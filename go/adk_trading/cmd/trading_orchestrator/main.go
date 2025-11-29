package main

import (
	"context"
	"flag"
	"log"
	"os"
	"path/filepath"

	"github.com/igorganapolsky/trading/adk_trading/internal/agents"
	"github.com/igorganapolsky/trading/adk_trading/internal/observability"
	"google.golang.org/adk/artifact"
	"google.golang.org/adk/cmd/launcher/adk"
	"google.golang.org/adk/cmd/launcher/full"
	"google.golang.org/adk/server/restapi/services"
	"google.golang.org/adk/session"
)

type config struct {
	modelName string
	dataDir   string
	logPath   string
	appName   string
}

func main() {
	ctx := context.Background()

	var cfg config
	flag.StringVar(&cfg.modelName, "model", envOrDefault("ADK_MODEL", "gemini-2.5-flash"), "Gemini model name to use for all agents.")
	flag.StringVar(&cfg.dataDir, "data_dir", envOrDefault("ADK_DATA_DIR", defaultDataDir()), "Path to the trading data directory.")
	flag.StringVar(&cfg.logPath, "log_path", envOrDefault("ADK_LOG_PATH", defaultLogPath()), "Destination JSONL log file for execution plans.")
	flag.StringVar(&cfg.appName, "app", envOrDefault("ADK_APP_NAME", "trading_orchestrator"), "App name to register with the ADK runtime.")
	flag.Parse()

	healthAddr := envOrDefault("ADK_HEALTH_ADDR", ":8091")
	obsRecorder := observability.NewRecorder(healthAddr)
	obsCtx, obsCancel := context.WithCancel(ctx)
	defer obsCancel()
	obsRecorder.Start(obsCtx)
	defer obsRecorder.Shutdown(context.Background())

	rootAgent, subAgents, err := agents.BuildTradingOrchestrator(ctx, agents.Config{
		AppName:               cfg.appName,
		ModelName:             cfg.modelName,
		DataDir:               cfg.dataDir,
		LogPath:               cfg.logPath,
		ObservabilityRecorder: obsRecorder,
	})
	if err != nil {
		log.Fatalf("failed to initialize trading orchestrator: %v", err)
	}

	agentLoader, err := services.NewMultiAgentLoader(rootAgent, subAgents...)
	if err != nil {
		log.Fatalf("failed to create agent loader: %v", err)
	}

	cfgADK := &adk.Config{
		AgentLoader:     agentLoader,
		SessionService:  session.InMemoryService(),
		ArtifactService: artifact.InMemoryService(),
	}

	launcher := full.NewLauncher()

	args := flag.Args()
	if len(args) == 0 {
		// Default to running the server if no args are provided
		args = []string{"server", "--http_port=8080"}
	}

	if err := launcher.Execute(ctx, cfgADK, args); err != nil {
		log.Fatalf("run failed: %v\n\n%s", err, launcher.CommandLineSyntax())
	}
}

func envOrDefault(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func defaultDataDir() string {
	return filepath.Join(projectRoot(), "data")
}

func defaultLogPath() string {
	return filepath.Join(projectRoot(), "logs", "adk_orchestrator.jsonl")
}

func projectRoot() string {
	wd, err := os.Getwd()
	if err != nil {
		log.Printf("warning: unable to determine working directory: %v", err)
		return "."
	}
	root := wd
	for {
		if _, err := os.Stat(filepath.Join(root, "data")); err == nil {
			return root
		}
		parent := filepath.Dir(root)
		if parent == root {
			break
		}
		root = parent
	}
	if modRoot := os.Getenv("TRADING_PROJECT_ROOT"); modRoot != "" {
		return modRoot
	}
	log.Println("warning: falling back to current working directory for project root discovery")
	return wd
}
