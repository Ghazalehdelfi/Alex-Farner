import asyncio
import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.agents.trend_analyzer_agent import trend_analyzer_agent

async def main():
    print("Welcome to the Social Media Trend Analyzer!")
    print("You can ask questions about social media trends and content strategy.")
    print("Example questions:")
    print("1. What are the current trends on LinkedIn for tech content?")
    print("2. Analyze the top 50 posts on LinkedIn about AI and machine learning")
    print("3. What type of content performs best on LinkedIn for software developers?")
    print("\nType 'exit' to quit.")
    
    while True:
        try:
            # Get user input
            user_input = input("\nWhat would you like to analyze? ").strip()
            
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
            
            if not user_input:
                print("Please enter a question.")
                continue
            
            # Get response from agent
            async for response in trend_analyzer_agent.run_async(user_input):
                print(response)
            
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try again with a different question.")

if __name__ == "__main__":
    asyncio.run(main()) 