FROM golang:1.24-alpine AS builder

WORKDIR /app

# Copy go.mod and go.sum
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the binary
RUN CGO_ENABLED=0 GOOS=linux go build -o adk-orchestrator ./cmd/trading_orchestrator

# Final stage
FROM alpine:latest

WORKDIR /app

# Copy binary
COPY --from=builder /app/adk-orchestrator .

# Install ca-certificates for HTTPS requests
RUN apk --no-cache add ca-certificates

# Expose port
EXPOSE 8080 8091

# Run
CMD ["./adk-orchestrator"]
