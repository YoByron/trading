package marketdata

import (
	"encoding/csv"
	"os"
	"path/filepath"
	"testing"
)

func TestMarketDataTool_LoadRows(t *testing.T) {
	// Create a temporary data directory structure
	tempDir := t.TempDir()
	historicalDir := filepath.Join(tempDir, "historical")
	if err := os.MkdirAll(historicalDir, 0755); err != nil {
		t.Fatalf("Failed to create historical directory: %v", err)
	}

	// Create a sample CSV file
	csvPath := filepath.Join(historicalDir, "SPY_2025-01-01.csv")
	file, err := os.Create(csvPath)
	if err != nil {
		t.Fatalf("Failed to create CSV file: %v", err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)

	// Write CSV with metadata rows and data rows
	writer.Write([]string{"# Metadata row 1"})
	writer.Write([]string{"# Metadata row 2"})
	writer.Write([]string{"# Metadata row 3"})
	writer.Write([]string{"Date", "Close", "High", "Low", "Open", "Volume"})
	writer.Write([]string{"2025-01-01", "450.00", "452.00", "448.00", "449.00", "1000000"})
	writer.Write([]string{"2025-01-02", "451.00", "453.00", "449.00", "450.00", "1100000"})
	writer.Write([]string{"2025-01-03", "452.00", "454.00", "450.00", "451.00", "1200000"})
	writer.Flush()
	file.Close()

	// Test loading rows
	rows, err := loadRows(tempDir, "SPY", 0)
	if err != nil {
		t.Fatalf("Failed to load rows: %v", err)
	}

	if len(rows) != 3 {
		t.Errorf("Expected 3 rows, got %d", len(rows))
	}

	if rows[0].Close != 450.00 {
		t.Errorf("Expected Close 450.00, got %f", rows[0].Close)
	}
}

func TestMarketDataTool_LoadRowsWithWindow(t *testing.T) {
	tempDir := t.TempDir()
	historicalDir := filepath.Join(tempDir, "historical")
	if err := os.MkdirAll(historicalDir, 0755); err != nil {
		t.Fatalf("Failed to create historical directory: %v", err)
	}

	csvPath := filepath.Join(historicalDir, "SPY_2025-01-01.csv")
	file, err := os.Create(csvPath)
	if err != nil {
		t.Fatalf("Failed to create CSV file: %v", err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)

	writer.Write([]string{"# Metadata"})
	writer.Write([]string{"# Metadata"})
	writer.Write([]string{"# Metadata"})
	writer.Write([]string{"Date", "Close", "High", "Low", "Open", "Volume"})
	// Write 10 rows
	for i := 1; i <= 10; i++ {
		writer.Write([]string{
			"2025-01-01",
			"450.00",
			"452.00",
			"448.00",
			"449.00",
			"1000000",
		})
	}
	writer.Flush()
	file.Close()

	// Test with window of 5
	rows, err := loadRows(tempDir, "SPY", 5)
	if err != nil {
		t.Fatalf("Failed to load rows: %v", err)
	}

	if len(rows) != 5 {
		t.Errorf("Expected 5 rows with window=5, got %d", len(rows))
	}
}

func TestMarketDataTool_LoadRowsNoData(t *testing.T) {
	tempDir := t.TempDir()

	_, err := loadRows(tempDir, "NONEXISTENT", 0)
	if err == nil {
		t.Error("Expected error for non-existent symbol")
	}
}

func TestMarketDataTool_ParseRow(t *testing.T) {
	tests := []struct {
		name    string
		record  []string
		wantErr bool
	}{
		{
			name:    "valid row",
			record:  []string{"2025-01-01", "450.00", "452.00", "448.00", "449.00", "1000000"},
			wantErr: false,
		},
		{
			name:    "invalid close",
			record:  []string{"2025-01-01", "invalid", "452.00", "448.00", "449.00", "1000000"},
			wantErr: true,
		},
		{
			name:    "too few fields",
			record:  []string{"2025-01-01", "450.00"},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := parseRow(tt.record)
			if (err != nil) != tt.wantErr {
				t.Errorf("parseRow() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestMarketDataTool_MovingAverage(t *testing.T) {
	rows := []Row{
		{Date: "2025-01-01", Close: 100.0},
		{Date: "2025-01-02", Close: 110.0},
		{Date: "2025-01-03", Close: 120.0},
		{Date: "2025-01-04", Close: 130.0},
		{Date: "2025-01-05", Close: 140.0},
	}

	result := movingAverage(rows, 3)
	expected := (120.0 + 130.0 + 140.0) / 3.0
	if result != expected {
		t.Errorf("Expected moving average %f, got %f", expected, result)
	}
}

func TestMarketDataTool_MovingAverageInsufficientData(t *testing.T) {
	rows := []Row{
		{Date: "2025-01-01", Close: 100.0},
		{Date: "2025-01-02", Close: 110.0},
	}

	result := movingAverage(rows, 5)
	expected := (100.0 + 110.0) / 2.0
	if result != expected {
		t.Errorf("Expected moving average %f with insufficient data, got %f", expected, result)
	}
}

func TestMarketDataTool_AverageTrueRange(t *testing.T) {
	rows := []Row{
		{Date: "2025-01-01", High: 102.0, Low: 98.0, Close: 100.0},
		{Date: "2025-01-02", High: 112.0, Low: 108.0, Close: 110.0},
		{Date: "2025-01-03", High: 122.0, Low: 118.0, Close: 120.0},
	}

	result := averageTrueRange(rows)
	if result <= 0 {
		t.Errorf("Expected positive ATR, got %f", result)
	}
}

func TestMarketDataTool_AverageTrueRangeInsufficientData(t *testing.T) {
	rows := []Row{
		{Date: "2025-01-01", High: 102.0, Low: 98.0, Close: 100.0},
	}

	result := averageTrueRange(rows)
	if result != 0 {
		t.Errorf("Expected 0 ATR for insufficient data, got %f", result)
	}
}

func TestMarketDataTool_New(t *testing.T) {
	tool, err := New("/tmp")
	if err != nil {
		t.Fatalf("Failed to create market data tool: %v", err)
	}
	if tool == nil {
		t.Error("Market data tool is nil")
	}

	_, err = New("")
	if err == nil {
		t.Error("Expected error for empty data directory")
	}
}
