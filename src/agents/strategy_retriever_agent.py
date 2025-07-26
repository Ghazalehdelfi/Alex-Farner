from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from typing import AsyncGenerator, Dict, Optional
from google.adk.events import Event, EventActions
import json
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyRetrieverAgent(BaseAgent):
    """A custom agent that retrieves and returns saved content strategies."""
    
    def __init__(self, name: str = "StrategyRetriever", strategies_dir: Optional[str] = None):
        """Initialize the strategy retriever agent.
        
        Args:
            name: The name of the agent
            strategies_dir: Directory containing saved strategies. Defaults to 'data/strategies'
        """
        super().__init__(name=name)
        self.strategies_dir = Path(strategies_dir or "data/strategies")
        self.strategies_dir.mkdir(parents=True, exist_ok=True)
        
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Implementation of the agent's main logic.
        
        Args:
            ctx: The invocation context containing session state and other information
            
        Yields:
            Events containing the retrieved strategy or error information
        """
        try:
            # Get strategy type from context state
            strategy_type = ctx.session.state.get("strategy_type")
            if not strategy_type:
                yield Event(
                    author=self.name,
                    content="No strategy type specified in context state",
                    actions=EventActions(escalate=True)
                )
                return
                
            # Look for strategy file
            strategy_file = self.strategies_dir / f"{strategy_type}_strategy.json"
            if not strategy_file.exists():
                yield Event(
                    author=self.name,
                    content=f"No saved strategy found for type: {strategy_type}",
                    actions=EventActions(escalate=True)
                )
                return
                
            # Read and return the strategy
            with open(strategy_file, 'r') as f:
                strategy = json.load(f)
                
            # Store strategy in session state
            ctx.session.state["retrieved_strategy"] = strategy
            
            yield Event(
                author=self.name,
                content=f"Successfully retrieved {strategy_type} strategy",
                actions=EventActions(escalate=False)
            )
            
        except Exception as e:
            logger.error(f"Error retrieving strategy: {str(e)}")
            yield Event(
                author=self.name,
                content=f"Error retrieving strategy: {str(e)}",
                actions=EventActions(escalate=True)
            )
            
    def _get_strategy_path(self, strategy_type: str) -> Path:
        """Get the path to a strategy file.
        
        Args:
            strategy_type: The type of strategy to retrieve
            
        Returns:
            Path object pointing to the strategy file
        """
        return self.strategies_dir / f"{strategy_type}_strategy.json"
        
    def save_strategy(self, strategy_type: str, strategy_data: Dict) -> bool:
        """Save a strategy to file.
        
        Args:
            strategy_type: The type of strategy to save
            strategy_data: The strategy data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            strategy_file = self._get_strategy_path(strategy_type)
            with open(strategy_file, 'w') as f:
                json.dump(strategy_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving strategy: {str(e)}")
            return False
            
    def get_available_strategies(self) -> list[str]:
        """Get a list of available strategy types.
        
        Returns:
            List of strategy type names
        """
        try:
            return [
                f.stem.replace("_strategy", "")
                for f in self.strategies_dir.glob("*_strategy.json")
            ]
        except Exception as e:
            logger.error(f"Error getting available strategies: {str(e)}")
            return [] 