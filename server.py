"""
Alfred MCP Server — Entry Point
Run with: python server.py
"""

from mcp.server.fastmcp import FastMCP
from alfread
.tools import register_all_tools
from alfread
.prompts import register_all_prompts
from alfread
.resources import register_all_resources
from alfread
.config import config

# Create the MCP server instance
mcp = FastMCP(
    name=config.SERVER_NAME,
    instructions=(
        "You are Alfred, a Batman-style butler AI assistant. "
        "You have access to a set of tools to help the user. "
        "Be formal, courteous, precise, and dryly witty — never casual."
    ),
)

# Register tools, prompts, and resources
register_all_tools(mcp)
register_all_prompts(mcp)
register_all_resources(mcp)

def main():
    mcp.run(transport='sse')

if __name__ == "__main__":
    main()