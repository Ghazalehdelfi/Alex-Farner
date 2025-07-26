from typing import Dict, Any, Optional
import yaml
from pathlib import Path
import logging
from datetime import datetime
import os
from google.adk.agents import LlmAgent

logger = logging.getLogger(__name__)

def get_strategies(name: str) -> Dict[str, Any]:
    """Load content strategies from YAML file."""
    try:
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = Path(project_root) / "src" / "config" / "content_strategies.yaml"
        
        if not config_path.exists():
            return {}
        with open(config_path, 'r') as f:
            strategies = yaml.safe_load(f)
            return strategies.get(name, {})
    except Exception as e:
        logger.error(f"Error loading strategies: {str(e)}")
        return {} 
def is_new_strategy(name: str) -> bool:
    """Check if the strategy is new."""
    return name is None

def get_insights(name: str) -> Dict[str, Any]:
    """Get insights for a strategy."""
    return {}


strategy_agent = LlmAgent(
    name="strategy_agent",
    description="A strategy agent that helps users create and optimize their content strategies.",
    model="gpt-4o-mini",
    system_prompt="You are an expert content strategy advisor. Your goal is to help users create and optimize their content strategies.",
    tools=[get_strategies, is_new_strategy, get_insights],
    verbose=True,
)