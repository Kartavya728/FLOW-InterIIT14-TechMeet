import pathway as pw
from pathway.xpacks.llm.mcp_server import McpServable, McpServer, PathwayMcp
pw.set_license_key("B4EB1A-A250F6-FF4EF4-2ACD7A-46912D-V3")
# Generate schema automatically from your CSV
schema = pw.schema_from_csv("data.csv")

# Load data stream with schema
table = pw.io.csv.read("data.csv", schema=schema, mode="streaming")

class EmptyRequestSchema(pw.Schema):
    pass

class MeanTool(McpServable):
    def get_mean(self, input_from_client: pw.Table) -> pw.Table:
        """Compute the mean of 'value' column in data.csv"""
        single_row_table = table.reduce(mean=pw.reducers.avg(pw.this.value))
        results = input_from_client.join_left(single_row_table, id=input_from_client.id).select(
            result=pw.if_else(pw.right.mean.is_none(), 0, pw.right.mean)
        )
        return results

    def register_mcp(self, server: McpServer):
        server.tool(
            "get_mean",
            request_handler=self.get_mean,
            schema=EmptyRequestSchema,
        )

function_to_serve = MeanTool()

pathway_mcp_server = PathwayMcp(
    name="Mean MCP Server",
    transport="streamable-http",
    host="localhost",
    port=8123,
    serve=[function_to_serve],
)

pw.run()
