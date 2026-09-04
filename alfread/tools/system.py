"""
System tools — time, environment info, shell commands, etc.
"""

import datetime
import platform


def register(mcp):

    @mcp.tool()
    def list_tools() -> dict:
        """Lista todas as ferramentas disponíveis no servidor MCP e seus status."""
        tools = mcp._tool_manager.list_tools() if hasattr(mcp, '_tool_manager') else []
        tool_names = [t.name if hasattr(t, 'name') else str(t) for t in tools]
        return {
            "status": "online",
            "total": len(tool_names),
            "tools": tool_names,
            "note": "Ferramentas do Playwright MCP e outros servidores externos também estão disponíveis mas são listadas separadamente."
        }

    @mcp.tool()
    def get_current_time() -> str:
        """Return the current date and time in ISO 8601 format."""
        return datetime.datetime.now().isoformat()

    @mcp.tool()
    def get_system_info() -> dict:
        """Return basic information about the host system."""
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        }
