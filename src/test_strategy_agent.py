import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.agents.linkedin_graph_agent import run_agent
import json

async def test_strategy_analysis():
    """Test the LinkedIn strategy analysis agent."""
    print("Starting LinkedIn strategy analysis test...")
    
    # Test query
    query = "Analyze my LinkedIn content performance and compare it with my current strategy"
    
    try:
        # Run the agent
        result = await run_agent(query)
        
        # Print results in a formatted way
        print("\n=== Strategy Analysis Results ===")
        
        if result.get("strategy_analysis"):
            analysis = result["strategy_analysis"].get("analysis", {})
            recommendations = result["strategy_analysis"].get("recommendations", [])
            
            print("\nPerformance Metrics:")
            print(f"Content Type: {analysis.get('content_type', 'N/A')}")
            print(f"Total Posts Analyzed: {analysis.get('total_posts', 0)}")
            print(f"Average Likes: {analysis.get('avg_likes', 0):.1f}")
            print(f"Average Comments: {analysis.get('avg_comments', 0):.1f}")
            
            print("\nEngagement Targets:")
            meets_targets = analysis.get('meets_engagement_target', {})
            print(f"Likes Target Met: {meets_targets.get('likes', False)}")
            print(f"Comments Target Met: {meets_targets.get('comments', False)}")
            
            print("\nTopic Performance:")
            for topic, metrics in analysis.get('top_performing_topics', {}).items():
                print(f"\n{topic}:")
                print(f"  Average Likes: {metrics.get('avg_likes', 0):.1f}")
                print(f"  Average Comments: {metrics.get('avg_comments', 0):.1f}")
                print(f"  Post Count: {metrics.get('post_count', 0)}")
            
            print("\nHashtag Performance:")
            for hashtag, metrics in analysis.get('hashtag_performance', {}).items():
                print(f"\n{hashtag}:")
                print(f"  Average Likes: {metrics.get('avg_likes', 0):.1f}")
                print(f"  Average Comments: {metrics.get('avg_comments', 0):.1f}")
                print(f"  Post Count: {metrics.get('post_count', 0)}")
            
            print("\nPrompt Analysis:")
            prompt_analysis = analysis.get('prompt_analysis', {})
            if prompt_analysis:
                print("\nCurrent Prompts:")
                print("\nSystem Prompt:")
                print(prompt_analysis.get('system_prompt', 'N/A'))
                print("\nUser Prompt:")
                print(prompt_analysis.get('user_prompt', 'N/A'))
                
                print("\nRequirements Met:")
                requirements = prompt_analysis.get('requirements_met', {})
                if 'length' in requirements:
                    length = requirements['length']
                    print(f"\nContent Length:")
                    print(f"  Meets Minimum: {length.get('min_length', False)}")
                    print(f"  Meets Maximum: {length.get('max_length', False)}")
                    print(f"  Average Length: {length.get('avg_length', 0):.1f} characters")
                
                if 'hashtags' in requirements:
                    hashtags = requirements['hashtags']
                    print(f"\nHashtag Usage:")
                    print(f"  Has Enough Hashtags: {hashtags.get('has_enough', False)}")
                    print(f"  Average Count: {hashtags.get('avg_count', 0):.1f}")
                
                if 'call_to_action' in requirements:
                    cta = requirements['call_to_action']
                    print(f"\nCall to Action:")
                    print(f"  Present: {cta.get('present', False)}")
                    print(f"  Percentage of Posts: {cta.get('percentage', 0):.1f}%")
            
            print("\nRecommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        else:
            print("No strategy analysis results found.")
        
        print("\n=== End of Analysis ===")
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_strategy_analysis()) 