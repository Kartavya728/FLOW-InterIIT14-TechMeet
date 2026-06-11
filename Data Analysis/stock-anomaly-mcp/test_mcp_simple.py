"""
Simple test to verify MCP server is working
"""
import pathway as pw
pw.set_license_key("B4EB1A-A250F6-FF4EF4-2ACD7A-46912D-V3")

from pathway.xpacks.llm.mcp_server import McpServable, McpServer, PathwayMcp

class SimpleTestTool(McpServable):
    
    def get_test_data(self, input_table: pw.Table) -> pw.Table:
        """Returns test data"""
        print("🔧 MCP Tool Called: get_test_data")
        
        test_with_content = input_table.select(
            content=pw.apply(
                lambda _: [{"type": "text", "text": "Hello from MCP server! Test successful."}],
                pw.this.id
            )
        )
        
        print("✓ Test data prepared for client")
        return test_with_content
    
    def register_mcp(self, server: McpServer):
        """Register MCP tools with the server"""
        print("📋 Registering MCP tools...")
        server.tool(
            "get_test_data",
            request_handler=self.get_test_data,
            schema=pw.Schema(),
        )
        print("✓ MCP tools registered: get_test_data")

print("🚀 Starting Simple MCP Test Server...")

try:
    test_tool = SimpleTestTool()
    print("✓ Test tool created")

    # Create and start the MCP server
    pathway_mcp_server = PathwayMcp(
        name="Simple Test MCP Server",
        transport="streamable-http",
        host="localhost",
        port=8070,
        serve=[test_tool],
    )
    print("✓ Pathway MCP server configured")

    print("\n✅ Server Status: ONLINE")
    print(f"🔗 MCP Endpoint: http://localhost:8070/mcp/")
    print("=" * 70)

    print("\n🎯 Server ready! Waiting for client connections...")
    print("=" * 70 + "\n")

    # Start the MCP server and run Pathway
    pw.run(monitoring_level=pw.MonitoringLevel.NONE)
    
except Exception as e:
    print(f"\n❌ Server startup failed: {e}")
    import traceback
    print(f"🐛 Traceback:\n{traceback.format_exc()}")
    raise
