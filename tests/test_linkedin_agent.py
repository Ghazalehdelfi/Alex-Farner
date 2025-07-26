import asyncio
import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.agents.linkedin_agent import LinkedInAgent

async def test_linkedin_agent():
    """Test the LinkedIn agent with Google's ADK."""
    print("Starting LinkedIn agent test...")
    
    # Initialize the agent
    agent = LinkedInAgent()
    
    # Test queries
    test_queries = [
        "Analyze my tech news content performance",
        "Analyze my ML tips content performance"
    ]
    
    # Create results directory if it doesn't exist
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    for query in test_queries:
        print(f"\nTesting query: {query}")
        try:
            result = await agent.run(query)
            
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                # Save results to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                content_type = "tech_news" if "tech" in query.lower() else "ml_tips"
                filename = results_dir / f"analysis_{content_type}_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    json.dump(result, f, indent=2)
                
                print(f"\nResults saved to {filename}")
                
                print("\nContent Analysis:")
                print(result["content_analysis"])
                
                print("\nEngagement Analysis:")
                print(result["engagement_analysis"])
                
                print("\nTop Performing Posts:")
                for i, post in enumerate(result["top_posts"], 1):
                    print(f"\n{i}. Engagement: {post['total_engagement']} (Likes: {post['likes']}, Comments: {post['comments']})")
                    print(f"Content: {post['content'][:200]}...")
                
                print("\nRecommendations:")
                for i, rec in enumerate(result["recommendations"], 1):
                    print(f"{i}. {rec}")
                
        except Exception as e:
            print(f"Error during analysis: {str(e)}")
    
    print("\nTest completed.")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_linkedin_agent()) 