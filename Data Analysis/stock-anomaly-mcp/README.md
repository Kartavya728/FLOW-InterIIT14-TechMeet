# Stock Anomaly Detection MCP System

This system provides real-time stock anomaly detection using Pathway MCP (Model Context Protocol) with streaming data.

## Components

1. **stock_streamer.py** - Fetches real stock data from Yahoo Finance and streams it to CSV
2. **server.py** - Pathway MCP server that processes streaming data and detects anomalies
3. **client.py** - MCP client that monitors and displays alerts
4. **anomaly_detector.py** - Statistical anomaly detection using Isolation Forest

## Quick Start

### Option 1: Run All Components Together
```bash
python test_integration.py
```

### Option 2: Run Components Separately (3 terminals)

**Terminal 1 - Start the streamer:**
```bash
python stock_streamer.py
```

**Terminal 2 - Start the MCP server:**
```bash
python server.py
```

**Terminal 3 - Start the MCP client:**
```bash
python client.py
```

## Expected Output

The system will display alerts in the format:
- `⚠️ ALERT: TSLA price jumped 5.2% in 1 minute`
- `✓ Normal: AAPL steady at $178.32`
- `⚠️ ALERT: GOOGL dropped 3.8% - unusual movement`

## Features

- **Real-time streaming**: Uses Yahoo Finance API for live stock data
- **Anomaly detection**: Statistical analysis using Isolation Forest algorithm
- **MCP protocol**: Uses Model Context Protocol for communication
- **Local processing**: Runs 100% locally on CPU, no cloud costs
- **Multiple stocks**: Monitors AAPL, GOOGL, MSFT, TSLA by default

## Dependencies

Install required packages:
```bash
pip install -r requirements.txt
```

## Configuration

- **Update interval**: 20 seconds (configurable in stock_streamer.py)
- **Anomaly threshold**: 15% contamination (configurable in server.py)
- **Window size**: 20 data points for anomaly detection
- **Stocks monitored**: AAPL, GOOGL, MSFT, TSLA (configurable in stock_streamer.py)
