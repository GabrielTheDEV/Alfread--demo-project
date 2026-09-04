"""
Data resources — expose static content or dynamic data via MCP resources.
"""


def register(mcp):

    @mcp.resource("alfred://info")
    def server_info() -> str:
        """Returns basic info about this MCP server."""
        return (
            "Alfred MCP Server\n"
            "A Batman-inspired AI butler assistant.\n"
            "Built with FastMCP."
        )
