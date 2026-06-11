"""
Real-Time Stock Anomaly Detection MCP Server
Fixed: Non-blocking MCP responses with proper data handling
"""
import pathway as pw
pw.set_license_key("B4EB1A-A250F6-FF4EF4-2ACD7A-46912D-V3")

from pathway.xpacks.llm.mcp_server import McpServable, McpServer, PathwayMcp
from anomaly_detector import StockAnomalyDetector
import json
import threading
import time

print("=" * 70)
print("🚀 Initializing Stock Anomaly Detection MCP Server")
print("=" * 70)

# Initialize detector with 40% alert rate
detector = StockAnomalyDetector(window_size=20, contamination=0.15)

class StockSchema(pw.Schema):
    symbol: str
    price: float
    volume: float
    timestamp: str

class AllStatsSchema(pw.Schema):
    pass 

print("\n📂 Reading stock data stream from data/ directory...")
stock_stream = pw.io.csv.read("data/", schema=StockSchema, mode="streaming")
print("✓ Stock stream connected")

@pw.udf
def detect_anomaly_udf(symbol: str, price: float) -> str:
    """Detect if price is anomalous"""
    print(f"\n🔍 Analyzing {symbol} at ${price:.2f}...")
    is_anomaly, score, pct_change = detector.update_and_detect(symbol, price)

    if is_anomaly:
        if pct_change > 0:
            message = f"⚠️ ALERT: {symbol} price jumped {abs(pct_change):.1f}% to ${price:.2f} (score: {score:.2f})"
        else:
            message = f"⚠️ ALERT: {symbol} dropped {abs(pct_change):.1f}% to ${price:.2f} (score: {score:.2f})"
        print(f"🔔 {message}")
    else:
        message = f"✓ Normal: {symbol} steady at ${price:.2f} ({pct_change:+.2f}%)"
        print(f"✅ {message}")
    
    return message

stock_stream = stock_stream.select(
    *pw.this,
    anomaly_result=detect_anomaly_udf(pw.this.symbol, pw.this.price)
)

@pw.udf
def print_alert(symbol: str, price: float, anomaly_result: str) -> str:
    """Print alert to console"""
    print(f"📢 Broadcasting: {anomaly_result}")
    return anomaly_result

stock_stream = stock_stream.select(
    *pw.this,
    printed_alert=print_alert(pw.this.symbol, pw.this.price, pw.this.anomaly_result)
)

# Pre-compute aggregated results for MCP tools
# This ensures data is always available without blocking
latest_alerts = stock_stream.groupby(pw.this.symbol).reduce(
    pw.this.symbol,
    latest_anomaly=pw.reducers.latest(pw.this.anomaly_result),
    latest_timestamp=pw.reducers.latest(pw.this.timestamp),
    latest_price=pw.reducers.latest(pw.this.price)
)

@pw.udf
def format_alert_line(symbol, anomaly, timestamp, price) -> str:
    return f"[{symbol}] {anomaly} @ {timestamp[:19]}"

# Format alerts
formatted_alerts = latest_alerts.select(
    alert_line=format_alert_line(
        pw.this.symbol,
        pw.this.latest_anomaly,
        pw.this.latest_timestamp,
        pw.this.latest_price
    )
)

# Aggregate all alerts into single result
all_alerts_aggregated = formatted_alerts.reduce(
    all_alerts=pw.reducers.sorted_tuple(pw.this.alert_line)
)

@pw.udf
def format_alerts_output(alert_tuple) -> str:
    if not alert_tuple or len(alert_tuple) == 0:
        return "⏳ Waiting for stock data..."
    alerts_list = list(alert_tuple)
    return "\n".join(alerts_list)

final_alerts = all_alerts_aggregated.select(
    result=format_alerts_output(pw.this.all_alerts)
)

# Pre-compute statistics
symbol_stats = stock_stream.groupby(pw.this.symbol).reduce(
    pw.this.symbol,
    count=pw.reducers.count(),
    avg_price=pw.reducers.avg(pw.this.price),
    min_price=pw.reducers.min(pw.this.price),
    max_price=pw.reducers.max(pw.this.price),
    latest_price=pw.reducers.latest(pw.this.price)
)

@pw.udf
def format_stat_line(symbol, count, avg, min_p, max_p, latest) -> str:
    return f"[{symbol}] Current: ${latest:.2f} | Avg: ${avg:.2f} | Range: ${min_p:.2f}-${max_p:.2f} | Points: {count}"

formatted_stats = symbol_stats.select(
    stat_line=format_stat_line(
        pw.this.symbol,
        pw.this.count,
        pw.this.avg_price,
        pw.this.min_price,
        pw.this.max_price,
        pw.this.latest_price
    )
)

all_stats_aggregated = formatted_stats.reduce(
    all_stats=pw.reducers.sorted_tuple(pw.this.stat_line)
)

@pw.udf
def format_stats_output(stat_tuple) -> str:
    if not stat_tuple or len(stat_tuple) == 0:
        return "⏳ No statistics available yet"
    stats_list = list(stat_tuple)
    return "\n".join(stats_list)

final_stats = all_stats_aggregated.select(
    result=format_stats_output(pw.this.all_stats)
)

class StockAnomalyTool(McpServable):
    
    def get_latest_alerts(self, input_table: pw.Table) -> pw.Table:
        """Returns latest anomaly alerts across all stocks"""
        print("\n🔧 MCP Tool Called: get_latest_alerts")
        
        # Join with the pre-computed alerts data
        alerts_with_content = input_table.join_left(final_alerts, id=input_table.id).select(
            content=pw.apply(
                lambda alerts_text: [{"type": "text", "text": alerts_text}] if alerts_text else [{"type": "text", "text": "⏳ Waiting for stock data..."}],
                pw.right.result
            )
        )
        
        print("✓ Alerts prepared for client")
        return alerts_with_content
    
    def get_symbol_stats(self, input_table: pw.Table) -> pw.Table:
        """Returns statistics for all symbols"""
        print("\n🔧 MCP Tool Called: get_symbol_stats")
        
        # Join with the pre-computed stats data
        stats_with_content = input_table.join_left(final_stats, id=input_table.id).select(
            content=pw.apply(
                lambda stats_text: [{"type": "text", "text": stats_text}] if stats_text else [{"type": "text", "text": "⏳ No statistics available yet"}],
                pw.right.result
            )
        )
        
        print("✓ Statistics prepared for client")
        return stats_with_content
    
    def register_mcp(self, server: McpServer):
        """Register MCP tools with the server"""
        print("\n📋 Registering MCP tools...")
        server.tool(
            "get_latest_alerts",
            request_handler=self.get_latest_alerts,
            schema=AllStatsSchema,
        )
        server.tool(
            "get_symbol_stats",
            request_handler=self.get_symbol_stats,
            schema=AllStatsSchema,
        )
        print("✓ MCP tools registered: get_latest_alerts, get_symbol_stats")

# Start MCP Server
print("\n" + "=" * 70)
print("🌐 Starting Stock Anomaly Detection MCP Server...")
print("=" * 70)

try:
    anomaly_tool = StockAnomalyTool()
    print("✓ Anomaly tool created")


    # Write alerts to CSV for logging
    pw.io.csv.write(stock_stream, "alerts_output.csv")
    print("💾 Logging alerts to: alerts_output.csv")

    # Create and start the MCP server
    pathway_mcp_server = PathwayMcp(
        name="Stock Anomaly MCP Server",
        transport="streamable-http",
        host="localhost",
        port=8070,
        serve=[anomaly_tool],
    )
    print("✓ Pathway MCP server configured")

    print("\n✅ Server Status: ONLINE")
    print(f"🔗 MCP Endpoint: http://localhost:8070/mcp/")
    print(f"📊 Monitoring stocks with ~40% alert rate")
    print(f"🔧 MCP tools use pre-computed results (non-blocking)")
    print("=" * 70)

    print("\n🎯 Server ready! Waiting for stock data and client connections...")
    print("=" * 70 + "\n")

    # Start the MCP server and run Pathway
    pw.run(monitoring_level=pw.MonitoringLevel.NONE)
    
except Exception as e:
    print(f"\n❌ Server startup failed: {e}")
    import traceback
    print(f"🐛 Traceback:\n{traceback.format_exc()}")
    raise