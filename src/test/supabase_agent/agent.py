from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import (MCPToolset, StdioServerParameters)
# from google.adk.tools import SseServerParams

supabase_agent = LlmAgent(
    model="gemini-2.0-flash",  # Specifies the LLM model to use
    name="greeter",            # A name for this specific agent
    instruction="""You are a database agent, you have access to two tables: posts and strategies.
      Any requests related to posts should be answered by querying the posts table, any requests related to strategies should be answered by querying the strategies table.
      The posts and strategies table are related by the strategy_name column.
      """, # The agent's primary instruction
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "@supabase/mcp-server-supabase@latest",
                    "--access-token",
                    "your_supabase_access_token_here",
                    "--project-ref",
                    "your_supabase_project_ref_here"
                ]
            )
            # tool_filter=['load_web_page'] # Optional: ensure only specific tools are loaded
        )
    ],             # The list of tools available to the agent
)

