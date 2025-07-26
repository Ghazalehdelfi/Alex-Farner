import asyncio
import json
from typing import Any
from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    SseServerParams,
)
from google.genai import types
from rich import print
from contextlib import AsyncExitStack
load_dotenv()
async def get_tools_async():
    """
    Gets tools from the File System MCP Server.
    This function initializes an MCPToolset with the SSE server parameters
    and then fetches the available tools.
    """
    toolset = MCPToolset(
        connection_params=SseServerParams(
            url="http://localhost:8001/mcp-server/mcp",
        )
    )
    tools = await toolset.get_tools()
    print("MCP Toolset created successfully.")
    return tools, toolset
async def get_agent_async():
    """
    Creates an ADK Agent equipped with tools from the MCP Server.
    It first fetches the tools and then initializes an LlmAgent
    with a specified model, name, instruction, and the fetched tools.
    """
    tools, toolset = await get_tools_async()
    print(f"Fetched {len(tools)} tools from MCP server.")
    for tool in tools:
        print(f"  - Discovered tool: {tool.name}")
    root_agent = LlmAgent(
        model="gemini-2.0-flash",  # Specifies the LLM model to use
        name="greeter",            # A name for this specific agent
        instruction="You are a greeting agent", # The agent's primary instruction
        tools=tools,               # The list of tools available to the agent
    )
    return root_agent, toolset
async def main(query: str):
    """
    Main asynchronous function to run the agent with a given query.
    It sets up the agent, session, and runner, then processes the query
    and prints the agent's final response.
    """
    async with AsyncExitStack() as cleanup_stack:
        # Get the agent and toolset, ensuring the toolset is closed on exit
        agent, toolset = await get_agent_async()
        cleanup_stack.push_async_callback(toolset.close)
        
        # Initialize an in-memory session service for managing conversation context
        session_service = InMemorySessionService()
        # Define constants for identifying the interaction context
        APP_NAME = "greeting_app"   # Application name
        USER_ID = "user_1"        # User identifier
        SESSION_ID = "session_001" # Session identifier (fixed for simplicity in this example)
        # Create the specific session where the conversation will happen
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID
        )
        print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")
        
        # Initialize the Runner to execute the agent
        runner = Runner(
            agent=agent,                 # The agent we want to run
            app_name=APP_NAME,           # Associates runs with our app
            session_service=session_service # Uses our session manager
        )
        
        # Prepare the user's message as a Content object
        content = types.Content(role='user', parts=[types.Part(text=query)])
        
        # Store all events from the agent's run
        all_events = []
        
        # Asynchronously run the agent with the new message and iterate through events
        async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
            print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")
            all_events.append(event)
        
        # After the loop, find the actual final response from all events
        final_response_events = [e for e in all_events if e.is_final_response()]
        
        final_response_text = ""
        for final_response_event in final_response_events:
        
            if final_response_event and final_response_event.content and final_response_event.content.parts:
                # Concatenate text from all parts of the final response
                final_response_text += "".join(part.text for part in final_response_event.content.parts if part.text)
            else:
                final_response_text = "No final response found or an error occurred."
        print(f"<<< Agent Response: {final_response_text}")
        
if __name__ == "__main__":
    # Run the main function with a sample query
    asyncio.run(main("I am Gopi"))