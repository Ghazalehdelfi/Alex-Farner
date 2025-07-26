import asyncio
import json
from typing import Any
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import (MCPToolset, StdioServerParameters)
# from google.adk.tools import SseServerParams
from google.genai import types
from rich import print
from contextlib import AsyncExitStack
# Get tools synchronously

# Create the root agent with the tools
root_agent = LlmAgent(
    model="gemini-2.0-flash",  # Specifies the LLM model to use
    name="greeter",            # A name for this specific agent
    instruction="You are a greeting agent", # The agent's primary instruction
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='python3', # Command to run your MCP server script
                args=["/Users/ghazalehdelfi/Desktop/ai-influencer/src/mcp/server.py"], # Argument is the path to the script
            )
            # tool_filter=['load_web_page'] # Optional: ensure only specific tools are loaded
        )
    ],             # The list of tools available to the agent
)
