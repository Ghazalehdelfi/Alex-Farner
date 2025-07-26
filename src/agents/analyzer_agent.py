from google.adk.agents import LlmAgent
from agents.trend_analyzer_agent import trend_analyzer_agent
from agents.post_history_retriever_agent import post_history_retriever_agent
from agents.strategy_retriever_agent import strategy_retriever_agent

analyzer_agent = LlmAgent(
    name="analyzer_agent",
    description="An agent that analyzes the trends and posts",
    model="gemini-2.0-flash",
    instruction="You are an expert in analyzing trends and posts",
    sub_agents=[trend_analyzer_agent, post_history_retriever_agent, strategy_retriever_agent],
)