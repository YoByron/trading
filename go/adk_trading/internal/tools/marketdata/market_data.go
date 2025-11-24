package marketdata

import (
	"encoding/csv"
	"errors"
	"fmt"
	"io"
	"math"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"

	"google.golang.org/adk/tool"
	"google.golang.org/adk/tool/functiontool"
)

type Input struct {
	Symbol     string `json:"symbol"`
	Window     int    `json:"window,omitempty"`
	IncludeRaw bool   `json:"includeRaw,omitempty"`
}

type Output struct {
	Symbol           string             `json:"symbol"`
	AsOf             time.Time          `json:"asOf"`
	Close            float64            `json:"close"`
	High             float64            `json:"high"`
	Low              float64            `json:"low"`
	Open             float64            `json:"open"`
	Volume           float64            `json:"volume"`
	Volatility       float64            `json:"volatility"`
	AverageTrueRange float64            `json:"averageTrueRange"`
	Returns          []float64          `json:"returns"`
	MovingAverages   map[string]float64 `json:"movingAverages"`
	VolumeRatio      float64            `json:"volumeRatio"`
	TrendStrength    float64            `json:"trendStrength"`
	RawRows          []Row              `json:"rawRows,omitempty"`
}

type Row struct {
	Date   string  `json:"date"`
	Close  float64 `json:"close"`
	High   float64 `json:"high"`
	Low    float64 `json:"low"`
	Open   float64 `json:"open"`
	Volume float64 `json:"volume"`
}

func New(dataDir string) (tool.Tool, error) {
	if dataDir == "" {
		return nil, errors.New("data directory not provided")
	}
	handler := func(ctx tool.Context, input Input) Output {
		window := input.Window
		if window <= 0 {
			window = 60
		}
		rows, err := loadRows(dataDir, input.Symbol, window)
		if err != nil {
			return Output{Symbol: strings.ToUpper(input.Symbol)}
		}
		stats := computeStats(rows)
		out := Output{
			Symbol:           strings.ToUpper(input.Symbol),
			AsOf:             stats.AsOf,
			Close:            stats.Close,
			High:             stats.High,
			Low:              stats.Low,
			Open:             stats.Open,
			Volume:           stats.Volume,
			Volatility:       stats.Volatility,
			AverageTrueRange: stats.AverageTrueRange,
			Returns:          stats.Returns,
			MovingAverages:   stats.MovingAverages,
			VolumeRatio:      stats.VolumeRatio,
			TrendStrength:    stats.TrendStrength,
		}
		if input.IncludeRaw {
			out.RawRows = rows
		}
		return out
	}
	return functiontool.New(functiontool.Config{
		Name:        "get_market_snapshot",
		Description: "Load recent OHLCV data and derived analytics for a symbol from the trading dataset.",
	}, handler)
}

type summary struct {
	AsOf             time.Time
	Close            float64
	High             float64
	Low              float64
	Open             float64
	Volume           float64
	Volatility       float64
	AverageTrueRange float64
	Returns          []float64
	MovingAverages   map[string]float64
	VolumeRatio      float64
	TrendStrength    float64
}

func loadRows(dataDir, symbol string, window int) ([]Row, error) {
	if symbol == "" {
		return nil, errors.New("symbol is required")
	}
	symbol = strings.ToUpper(symbol)
	glob := filepath.Join(dataDir, "historical", fmt.Sprintf("%s_*.csv", symbol))
	matches, err := filepath.Glob(glob)
	if err != nil || len(matches) == 0 {
		return nil, fmt.Errorf("no historical data for %s", symbol)
	}
	sort.Strings(matches)
	path := matches[len(matches)-1]

	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open historical data: %w", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	reader.FieldsPerRecord = -1
	var records [][]string
	for {
		record, err := reader.Read()
		if errors.Is(err, io.EOF) {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("read csv: %w", err)
		}
		records = append(records, record)
	}
	if len(records) <= 3 {
		return nil, fmt.Errorf("insufficient data in %s", path)
	}
	records = records[3:] // skip metadata rows
	if len(records) == 0 {
		return nil, fmt.Errorf("no price rows in %s", path)
	}
	if window > 0 && len(records) > window {
		records = records[len(records)-window:]
	}
	rows := make([]Row, 0, len(records))
	for _, rec := range records {
		if len(rec) < 6 {
			continue
		}
		row, err := parseRow(rec)
		if err != nil {
			continue
		}
		rows = append(rows, row)
	}
	return rows, nil
}

func parseRow(rec []string) (Row, error) {
	if len(rec) < 6 {
		return Row{}, fmt.Errorf("insufficient fields: need 6, got %d", len(rec))
	}
	closeVal, err := strconv.ParseFloat(rec[1], 64)
	if err != nil {
		return Row{}, err
	}
	highVal, err := strconv.ParseFloat(rec[2], 64)
	if err != nil {
		return Row{}, err
	}
	lowVal, err := strconv.ParseFloat(rec[3], 64)
	if err != nil {
		return Row{}, err
	}
	openVal, err := strconv.ParseFloat(rec[4], 64)
	if err != nil {
		return Row{}, err
	}
	volumeVal, err := strconv.ParseFloat(rec[5], 64)
	if err != nil {
		return Row{}, err
	}
	return Row{
		Date:   rec[0],
		Close:  closeVal,
		High:   highVal,
		Low:    lowVal,
		Open:   openVal,
		Volume: volumeVal,
	}, nil
}

func computeStats(rows []Row) summary {
	n := len(rows)
	if n == 0 {
		return summary{MovingAverages: map[string]float64{}}
	}
	last := rows[n-1]

	returns := make([]float64, 0, n-1)
	var sumReturn, sumReturnSq float64
	for i := 1; i < n; i++ {
		ret := (rows[i].Close / rows[i-1].Close) - 1.0
		returns = append(returns, ret)
		sumReturn += ret
		sumReturnSq += ret * ret
	}
	var volatility float64
	if len(returns) > 1 {
		mean := sumReturn / float64(len(returns))
		variance := (sumReturnSq / float64(len(returns))) - (mean * mean)
		if variance < 0 {
			variance = 0
		}
		volatility = math.Sqrt(variance) * math.Sqrt(252.0)
	}

	atr := averageTrueRange(rows)
	movingAverages := map[string]float64{
		"ma20":  movingAverage(rows, 20),
		"ma50":  movingAverage(rows, 50),
		"ma100": movingAverage(rows, 100),
	}

	var volumeRatio float64 = 1.0
	if n >= 21 {
		var sumVolume float64
		for i := n - 21; i < n-1; i++ {
			sumVolume += rows[i].Volume
		}
		avgVolume := sumVolume / 20
		if avgVolume > 0 {
			volumeRatio = rows[n-1].Volume / avgVolume
		}
	}

	maShort := movingAverages["ma20"]
	maLong := movingAverages["ma50"]
	var trendStrength float64
	if maLong != 0 {
		trendStrength = (maShort - maLong) / maLong
	}

	asOf, _ := time.Parse("2006-01-02", last.Date)
	return summary{
		AsOf:             asOf,
		Close:            last.Close,
		High:             last.High,
		Low:              last.Low,
		Open:             last.Open,
		Volume:           last.Volume,
		Volatility:       volatility,
		AverageTrueRange: atr,
		Returns:          returns,
		MovingAverages:   movingAverages,
		VolumeRatio:      volumeRatio,
		TrendStrength:    trendStrength,
	}
}

func movingAverage(rows []Row, period int) float64 {
	if period <= 0 {
		return 0
	}
	if len(rows) < period {
		period = len(rows)
	}
	if period == 0 {
		return 0
	}
	var sum float64
	for i := len(rows) - period; i < len(rows); i++ {
		sum += rows[i].Close
	}
	return sum / float64(period)
}

func averageTrueRange(rows []Row) float64 {
	if len(rows) < 2 {
		return 0
	}
	var trs []float64
	for i := 1; i < len(rows); i++ {
		high := rows[i].High
		low := rows[i].Low
		prevClose := rows[i-1].Close

		tr := math.Max(high-low, math.Max(math.Abs(high-prevClose), math.Abs(low-prevClose)))
		trs = append(trs, tr)
	}
	var sum float64
	for _, tr := range trs {
		sum += tr
	}
	return sum / float64(len(trs))
}
