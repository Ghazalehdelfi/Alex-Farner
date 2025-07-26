from typing import Dict, List, Optional, Any
from google.adk import Agent, Tool, ToolCall
from google.adk.tools import ToolRegistry
from google.cloud import aiplatform
from google.genai import GenerativeModel
import yaml
import os
from pathlib import Path
import logging
import json
from datetime import datetime
import asyncio
from dataclasses import dataclass
from enum import Enum

from src.agents.trend_analyzer_agent import DataCollectorAgent
from src.agents.analyzer_agent import AnalyzerAgent
from src.agents.suggestion_agent import SuggestionAgent

# --- SETUP ---
logging.basicConfig(level=logging.INFO)

class MessageType(Enum):
    DATA_REQUEST = "data_request"
    DATA_RESPONSE = "data_response"
    ANALYSIS_REQUEST = "analysis_request"
    ANALYSIS_RESPONSE = "analysis_response"
    SUGGESTION_REQUEST = "suggestion_request"
    SUGGESTION_RESPONSE = "suggestion_response"
    ERROR = "error"

@dataclass
class AgentMessage:
    sender: str
    recipient: str
    msg_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime = datetime.now()

class OrchestratorAgent(Agent):
    """Agent responsible for orchestrating communication between different agents."""
    
    def __init__(self):
        super().__init__()
        self.model = GenerativeModel('gemini-pro')
        self.tool_registry = self._setup_tools()
        
        # Initialize sub-agents
        self.data_collector = DataCollectorAgent()
        self.analyzer = AnalyzerAgent()
        self.suggestion = SuggestionAgent()
        
        # Message bus for inter-agent communication
        self.message_bus: Dict[str, List[AgentMessage]] = {
            "data_collector": [],
            "analyzer": [],
            "suggestion": []
        }
        
        # Create workflow state directory
        self.state_dir = Path("data/workflow_state")
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_tools(self) -> ToolRegistry:
        """Set up the agent's tools."""
        registry = ToolRegistry()
        
        # Add message handling tools
        registry.register_tool(
            Tool(
                name="send_message",
                description="Send a message to another agent",
                parameters={
                    "sender": {"type": "string", "description": "Sender agent name"},
                    "recipient": {"type": "string", "description": "Recipient agent name"},
                    "msg_type": {"type": "string", "description": "Type of message"},
                    "content": {"type": "object", "description": "Message content"}
                },
                handler=self._send_message
            )
        )
        
        registry.register_tool(
            Tool(
                name="get_messages",
                description="Get messages for an agent",
                parameters={
                    "agent_name": {"type": "string", "description": "Name of the agent"},
                    "msg_type": {"type": "string", "description": "Type of messages to retrieve"},
                    "clear_messages": {"type": "boolean", "description": "Whether to clear messages after retrieval"}
                },
                handler=self._get_messages
            )
        )
        
        return registry
    
    async def _send_message(self, sender: str, recipient: str, msg_type: str, content: Dict) -> Dict:
        """Send a message to another agent."""
        try:
            message = AgentMessage(
                sender=sender,
                recipient=recipient,
                msg_type=MessageType(msg_type),
                content=content
            )
            
            self.message_bus[recipient].append(message)
            return {"status": "success", "message_id": str(message.timestamp)}
            
        except Exception as e:
            logging.error(f"Error sending message: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _get_messages(self, agent_name: str, msg_type: Optional[str] = None, clear_messages: bool = True) -> List[Dict]:
        """Get messages for an agent."""
        try:
            messages = self.message_bus[agent_name]
            
            if msg_type:
                messages = [msg for msg in messages if msg.msg_type.value == msg_type]
            
            result = [
                {
                    "sender": msg.sender,
                    "msg_type": msg.msg_type.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in messages
            ]
            
            if clear_messages:
                self.message_bus[agent_name] = []
            
            return result
            
        except Exception as e:
            logging.error(f"Error getting messages: {str(e)}")
            return []
    
    async def _handle_agent_request(self, agent_name: str, request: Dict) -> Dict:
        """Handle a request from an agent."""
        try:
            if agent_name == "data_collector":
                return await self.data_collector.run(request["query"])
            elif agent_name == "analyzer":
                return await self.analyzer.run(request["query"])
            elif agent_name == "suggestion":
                return await self.suggestion.run(request["query"])
            else:
                return {"error": f"Unknown agent: {agent_name}"}
                
        except Exception as e:
            logging.error(f"Error handling agent request: {str(e)}")
            return {"error": str(e)}
    
    async def run(self, query: str) -> Dict:
        """Run the orchestrator with the given query."""
        try:
            # Parse the query to determine which agent should handle it
            if "collect" in query.lower():
                agent_name = "data_collector"
            elif "analyze" in query.lower():
                agent_name = "analyzer"
            elif "suggest" in query.lower():
                agent_name = "suggestion"
            else:
                return {"error": "Could not determine which agent should handle the query"}
            
            # Create a workflow state
            workflow_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            state = {
                "workflow_id": workflow_id,
                "query": query,
                "agent": agent_name,
                "status": "started",
                "messages": [],
                "results": {}
            }
            
            # Handle the request
            result = await self._handle_agent_request(agent_name, {"query": query})
            
            # Update state
            state["status"] = "completed" if "error" not in result else "failed"
            state["results"] = result
            
            # Save workflow state
            await self._save_workflow_state(state, workflow_id)
            
            return state
            
        except Exception as e:
            logging.error(f"Error in run: {str(e)}")
            return {"error": str(e)}
    
    async def _save_workflow_state(self, state: Dict, workflow_id: str) -> str:
        """Save the current workflow state."""
        filename = self.state_dir / f"workflow_{workflow_id}.json"
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
        
        return str(filename) 