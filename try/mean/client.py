# client.py
import asyncio
from fastmcp import Client

PATHWAY_MCP_URL = "http://localhost:8123/mcp/"

async def main():
    client = Client(PATHWAY_MCP_URL)
    async with client:
        result = await client.call_tool(name="get_mean", arguments={})
        print("Mean value:", result.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
