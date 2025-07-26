from fastmcp import FastMCP
from fastapi import FastAPI
from starlette.routing import Mount
# Create your FastMCP server as well as any tools, resources, etc.
mcp = FastMCP("GreetingServer")
@mcp.tool()
def hello(name: str) -> str:
    """
    A simple tool that returns a greeting message.
    Args:
        name: The name to greet.
    Returns:
        A string with the greeting.
    """
    return f"Hello, {name}!"


if __name__ == "__main__":
    mcp.run()