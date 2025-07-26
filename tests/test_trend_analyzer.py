import pytest
import asyncio
import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.agents.trend_analyzer_agent import trend_analyzer_agent

async def test_trend_analyzer_basic():
    """Test basic trend analysis functionality."""
    # Test case 1: Analyze LinkedIn trends
    response = await trend_analyzer_agent.run(
        "What are the current trends on LinkedIn for tech content?"
    )
    assert response is not None
    print("\nTest Case 1 - LinkedIn Tech Trends:")
    print(response)

    # Test case 2: Analyze specific number of posts
    response = await trend_analyzer_agent.run(
        "Analyze the top 50 posts on LinkedIn about AI and machine learning"
    )
    assert response is not None
    print("\nTest Case 2 - AI/ML Content Analysis:")
    print(response)

    # Test case 3: Content strategy recommendations
    response = await trend_analyzer_agent.run(
        "What type of content performs best on LinkedIn for software developers?"
    )
    assert response is not None
    print("\nTest Case 3 - Developer Content Strategy:")
    print(response)

async def test_trend_analyzer_error_handling():
    """Test error handling for invalid requests."""
    # Test case 4: Invalid platform
    response = await trend_analyzer_agent.run(
        "What are the trends on Twitter?"  # Twitter not supported yet
    )
    assert response is not None
    print("\nTest Case 4 - Invalid Platform:")
    print(response)

    # Test case 5: Invalid request format
    response = await trend_analyzer_agent.run(
        "Show me some posts"  # Too vague
    )
    assert response is not None
    print("\nTest Case 5 - Vague Request:")
    print(response)

def main():
    """Run all tests."""
    print("Starting Trend Analyzer Agent Tests...")
    
    # Run basic functionality tests
    print("\nRunning Basic Functionality Tests...")
    asyncio.run(test_trend_analyzer_basic())
    
    # Run error handling tests
    print("\nRunning Error Handling Tests...")
    asyncio.run(test_trend_analyzer_error_handling())
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main() 