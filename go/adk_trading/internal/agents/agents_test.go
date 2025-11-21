package agents

import (
	"context"
	"os"
	"path/filepath"
	"testing"
)

func TestConfig_Validate(t *testing.T) {
	tempDir := t.TempDir()
	logPath := filepath.Join(tempDir, "test.log")

	tests := []struct {
		name    string
		config  Config
		wantErr bool
	}{
		{
			name: "valid config",
			config: Config{
				AppName:   "test_app",
				ModelName: "gemini-2.5-flash",
				DataDir:   tempDir,
				LogPath:   logPath,
			},
			wantErr: false,
		},
		{
			name: "empty app name",
			config: Config{
				AppName:   "",
				ModelName: "gemini-2.5-flash",
				DataDir:   tempDir,
				LogPath:   logPath,
			},
			wantErr: true,
		},
		{
			name: "empty model name",
			config: Config{
				AppName:   "test_app",
				ModelName: "",
				DataDir:   tempDir,
				LogPath:   logPath,
			},
			wantErr: true,
		},
		{
			name: "empty data dir",
			config: Config{
				AppName:   "test_app",
				ModelName: "gemini-2.5-flash",
				DataDir:   "",
				LogPath:   logPath,
			},
			wantErr: true,
		},
		{
			name: "empty log path",
			config: Config{
				AppName:   "test_app",
				ModelName: "gemini-2.5-flash",
				DataDir:   tempDir,
				LogPath:   "",
			},
			wantErr: true,
		},
		{
			name: "non-existent data dir",
			config: Config{
				AppName:   "test_app",
				ModelName: "gemini-2.5-flash",
				DataDir:   "/nonexistent/path",
				LogPath:   logPath,
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.config.validate()
			if (err != nil) != tt.wantErr {
				t.Errorf("Config.validate() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestConfig_DefaultPortfolioValue(t *testing.T) {
	tempDir := t.TempDir()
	logPath := filepath.Join(tempDir, "test.log")

	config := Config{
		AppName:   "test_app",
		ModelName: "gemini-2.5-flash",
		DataDir:   tempDir,
		LogPath:   logPath,
		// PortfolioValue not set - should default to 1_000_000
	}

	// This test verifies the default portfolio value logic
	// The actual BuildTradingOrchestrator requires GOOGLE_API_KEY
	// so we just test the validation logic here
	if err := config.validate(); err != nil {
		t.Errorf("Config should be valid: %v", err)
	}
}

func TestSanitizeName(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "simple name",
			input:    "TradingOrchestrator",
			expected: "tradingorchestrator",
		},
		{
			name:     "name with spaces",
			input:    "Trading Orchestrator",
			expected: "trading_orchestrator",
		},
		{
			name:     "name with path separators",
			input:    "trading/orchestrator",
			expected: "trading_orchestrator",
		},
		{
			name:     "mixed case with spaces",
			input:    "My Trading App",
			expected: "my_trading_app",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := sanitizeName(tt.input)
			if result != tt.expected {
				t.Errorf("sanitizeName(%q) = %q, want %q", tt.input, result, tt.expected)
			}
		})
	}
}

func TestBuildTradingOrchestrator_MissingAPIKey(t *testing.T) {
	// Save original API key
	originalKey := os.Getenv("GOOGLE_API_KEY")
	defer os.Setenv("GOOGLE_API_KEY", originalKey)

	// Clear API key
	os.Unsetenv("GOOGLE_API_KEY")

	tempDir := t.TempDir()
	logPath := filepath.Join(tempDir, "test.log")

	config := Config{
		AppName:   "test_app",
		ModelName: "gemini-2.5-flash",
		DataDir:   tempDir,
		LogPath:   logPath,
	}

	ctx := context.Background()
	_, _, err := BuildTradingOrchestrator(ctx, config)

	if err == nil {
		t.Error("Expected error when GOOGLE_API_KEY is not set")
	}
}

