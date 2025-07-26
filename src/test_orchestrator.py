import asyncio
import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.agents.orchestrator_agent import OrchestratorAgent

async def test_agent_interaction():
    """Test interactive communication between agents."""
    print("Starting agent interaction test...")
    
    # Initialize the orchestrator
    orchestrator = OrchestratorAgent()
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Data Collection Request",
            "query": "collect recent tech news posts",
            "expected_agent": "data_collector"
        },
        {
            "name": "Analysis Request",
            "query": "analyze engagement patterns in tech news",
            "expected_agent": "analyzer"
        },
        {
            "name": "Suggestion Request",
            "query": "suggest content improvements for tech news",
            "expected_agent": "suggestion"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\nTesting scenario: {scenario['name']}")
        print(f"Query: {scenario['query']}")
        
        try:
            # Run the initial query
            result = await orchestrator.run(scenario['query'])
            
            if "error" in result:
                print(f"Error: {result['error']}")
                continue
            
            print(f"\nInitial request handled by: {result['agent']}")
            print(f"Status: {result['status']}")
            
            # Simulate agent interaction
            if result['agent'] == "analyzer":
                # Analyzer requests data from collector
                print("\nAnalyzer requesting data from collector...")
                await orchestrator._send_message(
                    sender="analyzer",
                    recipient="data_collector",
                    msg_type="data_request",
                    content={"request": "get_recent_posts", "content_type": "tech_news"}
                )
                
                # Check messages for data_collector
                messages = await orchestrator._get_messages("data_collector")
                print(f"Messages for data_collector: {len(messages)}")
                
                # Simulate data collector response
                await orchestrator._send_message(
                    sender="data_collector",
                    recipient="analyzer",
                    msg_type="data_response",
                    content={"posts": [{"id": 1, "content": "Sample post"}]}
                )
                
            elif result['agent'] == "suggestion":
                # Suggestion agent requests analysis from analyzer
                print("\nSuggestion agent requesting analysis from analyzer...")
                await orchestrator._send_message(
                    sender="suggestion",
                    recipient="analyzer",
                    msg_type="analysis_request",
                    content={"request": "get_engagement_analysis", "content_type": "tech_news"}
                )
                
                # Check messages for analyzer
                messages = await orchestrator._get_messages("analyzer")
                print(f"Messages for analyzer: {len(messages)}")
                
                # Simulate analyzer response
                await orchestrator._send_message(
                    sender="analyzer",
                    recipient="suggestion",
                    msg_type="analysis_response",
                    content={"analysis": {"engagement_rate": 0.05}}
                )
            
            # Print final state
            print("\nFinal State:")
            print(f"Workflow ID: {result['workflow_id']}")
            print(f"Results: {json.dumps(result['results'], indent=2)}")
            
        except Exception as e:
            print(f"Error during scenario: {str(e)}")
    
    print("\nTest completed.")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_agent_interaction()) 