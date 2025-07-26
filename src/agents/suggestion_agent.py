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
import glob
from google.adk.agent import LlmAgent
# --- SETUP ---
logging.basicConfig(level=logging.INFO)

def get_prompt(strategy: dict) -> str:
    """Get the prompt defined in the strategy config file"""
    return strategy.get("prompt", "")

def get_strategy(name: str) -> dict:
    """Get the strategy defined in the strategy config file"""
    try:
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = Path(project_root) / "src" / "config" / "content_strategies.yaml"
        
        if not config_path.exists():
            return ""
        with open(config_path, 'r') as f:
            strategies = yaml.safe_load(f)
            return strategies.get(name, {}).get("strategy", "")
    except Exception as e:
        logging.error(f"Error loading strategy: {str(e)}")
        return ""
def save_content(content: str) -> str:
    """Save the content to the database"""
    return "Content saved"

suggestion_agent = LlmAgent(
    name="suggestion_agent",
    description="A suggestion agent that helps users create and optimize their content strategies.",
    model="gpt-4o-mini",
    system_prompt="You are an expert content strategy advisor. Your goal is to help users create and optimize their content strategies.",
    tools=[get_strategy, get_prompt, save_content],
    verbose=True,
)