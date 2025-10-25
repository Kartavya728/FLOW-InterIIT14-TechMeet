"""
Test client for Stock Anomaly MCP Server
Using requests for HTTP communication with Pathway MCP server
"""
import asyncio
import aiohttp
import json
from datetime import datetime

PATHWAY_MCP_URL = "http://localhost:8070/mcp/"

def print_header():
    """Print a nice header"""
    print("\n" + "=" * 70)
    print("📈 Stock Anomaly Detection - MCP Client Monitor")
    print("=" * 70)
    print(f"🔗 Connected to: {PATHWAY_MCP_URL}")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")

def print_separator():
    """Print a visual separator"""
    print("\n" + "-" * 70)

async def get_alerts(session):
    """Fetch and display latest alerts"""
    try:
        print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] Fetching latest alerts...")
        
        # Make HTTP request to Pathway MCP server
        async with session.post(
            f"{PATHWAY_MCP_URL}call_tool",
            json={
                "name": "get_latest_alerts",
                "arguments": {}
            },
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                
                if result and "content" in result:
                    content_items = result["content"]
                    
                    if isinstance(content_items, list) and len(content_items) > 0:
                        print("\n" + "🔔" * 35)
                        print("               LATEST ALERTS")
                        print("🔔" * 35 + "\n")
                        
                        for item in content_items:
                            if isinstance(item, dict):
                                # Handle MCP content format: {"type": "text", "text": "..."}
                                if item.get("type") == "text":
                                    text = item.get("text", "")
                                else:
                                    text = item.get("text") or item.get("content") or str(item)
                            else:
                                text = str(item)
                            
                            if text.strip():  # Only print non-empty text
                                print(text)
                        
                        print("\n" + "=" * 70)
                        return True
                    else:
                        print("⏳ No alert data in response")
                elif isinstance(result, str):
                    # Direct string response
                    print("\n" + "🔔" * 35)
                    print("               LATEST ALERTS")
                    print("🔔" * 35 + "\n")
                    print(result)
                    print("\n" + "=" * 70)
                    return True
                
                print("⏳ No alerts available yet")
                if result:
                    print(f"🐛 Debug - Full result: {result}")
                return False
            else:
                print(f"❌ HTTP Error {response.status}: {await response.text()}")
                return False
                
    except Exception as e:
        print(f"❌ Error fetching alerts: {e}")
        import traceback
        print(f"🐛 Traceback:\n{traceback.format_exc()}")
        return False

async def get_statistics(session):
    """Fetch and display symbol statistics"""
    try:
        print(f"\n📊 [{datetime.now().strftime('%H:%M:%S')}] Fetching statistics...")
        
        # Make HTTP request to Pathway MCP server
        async with session.post(
            f"{PATHWAY_MCP_URL}call_tool",
            json={
                "name": "get_symbol_stats",
                "arguments": {}
            },
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                
                if result and "content" in result:
                    content_items = result["content"]
                    
                    if isinstance(content_items, list) and len(content_items) > 0:
                        print("\n" + "📊" * 35)
                        print("            SYMBOL STATISTICS")
                        print("📊" * 35 + "\n")
                        
                        for item in content_items:
                            if isinstance(item, dict):
                                # Handle MCP content format: {"type": "text", "text": "..."}
                                if item.get("type") == "text":
                                    text = item.get("text", "")
                                else:
                                    text = item.get("text") or item.get("content") or str(item)
                            else:
                                text = str(item)
                            
                            if text.strip():  # Only print non-empty text
                                print(text)
                        
                        print("\n" + "=" * 70)
                        return True
                elif isinstance(result, str):
                    print("\n" + "📊" * 35)
                    print("            SYMBOL STATISTICS")
                    print("📊" * 35 + "\n")
                    print(result)
                    print("\n" + "=" * 70)
                    return True
                
                print("⏳ No statistics available yet")
                return False
            else:
                print(f"❌ HTTP Error {response.status}: {await response.text()}")
                return False
                
    except Exception as e:
        print(f"❌ Error fetching statistics: {e}")
        return False

async def monitor_stocks():
    """Main monitoring loop"""
    print_header()
    
    # Create HTTP session
    async with aiohttp.ClientSession() as session:
        try:
            # Test connection first
            print("🔌 Testing connection to MCP server...")
            async with session.get(f"{PATHWAY_MCP_URL}list_tools") as response:
                if response.status == 200:
                    tools_data = await response.json()
                    tools = tools_data.get("tools", [])
                    print(f"✅ Connected! Available tools: {[tool.get('name', 'unknown') for tool in tools]}")
                else:
                    print(f"⚠️ Server responded with status {response.status}")
            
            print("\n✅ Connected! Starting monitoring loop...\n")
            
            iteration = 0
            stats_interval = 3  # Show stats every 3 iterations
            consecutive_failures = 0
            max_failures = 3
            
            while True:
                try:
                    iteration += 1
                    
                    print_separator()
                    print(f"🔄 Monitoring Cycle #{iteration}")
                    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print_separator()
                    
                    # Get latest alerts
                    alerts_fetched = await get_alerts(session)
                    
                    if alerts_fetched:
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                    
                    # Periodically show statistics
                    if iteration % stats_interval == 0:
                        stats_fetched = await get_statistics(session)
                        if stats_fetched:
                            consecutive_failures = 0
                    
                    # Check for persistent failures
                    if consecutive_failures >= max_failures:
                        print(f"\n⚠️  Warning: {consecutive_failures} consecutive failures")
                        print("🔄 Server might be starting up or processing data...")
                    
                    # Visual feedback
                    if alerts_fetched:
                        print("\n✨ Alert check complete")
                    else:
                        print("\n⏳ Waiting for data...")
                    
                    # Wait before next check
                    wait_time = 5
                    print(f"\n💤 Sleeping for {wait_time} seconds...")
                    next_check = datetime.now().timestamp() + wait_time
                    print(f"⏰ Next check in {wait_time}s")
                    
                    for i in range(wait_time):
                        print(".", end="", flush=True)
                        await asyncio.sleep(1)
                    print()  # New line after dots
                    
                except KeyboardInterrupt:
                    print("\n\n" + "=" * 70)
                    print("🛑 Monitor stopped by user")
                    print(f"📊 Total monitoring cycles: {iteration}")
                    print("=" * 70)
                    break
                    
                except Exception as e:
                    print(f"\n❌ Unexpected error: {e}")
                    import traceback
                    print(f"🐛 Traceback:\n{traceback.format_exc()}")
                    print("🔄 Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            print(f"\n❌ Connection failed: {e}")
            print("Please ensure server is running at:")
            print(f"   {PATHWAY_MCP_URL}")

if __name__ == "__main__":
    print("\n🚀 Starting Stock Anomaly Monitor Client...")
    print("📡 Using aiohttp for HTTP communication")
    try:
        asyncio.run(monitor_stocks())
    except KeyboardInterrupt:
        print("\n✅ Client shutdown complete")