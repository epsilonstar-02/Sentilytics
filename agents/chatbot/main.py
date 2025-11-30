import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to sys.path to allow importing modules from the project
# Use insert(0) to prioritize project root over current directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from google.adk.runners import InMemoryRunner
from google.genai import types
from agents.chatbot.agents import coordinator_agent

# Configure logging - set to WARNING to reduce noise
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def main():
    print("=" * 50)
    print("YouTube Analytics Chatbot")
    print("=" * 50)
    print("\nAvailable products: iPhone 17 Pro, MacBook Pro M5, ChatGPT GPT-5")
    print("Data period: October 23, 2025 - November 4, 2025")
    print("\nExample queries:")
    print("  - What are the top 5 most viewed iPhone 17 Pro videos?")
    print("  - What do people think about iPhone 17?")
    print("  - Compare iPhone 17 vs iPhone 17 Pro")
    print("  - Show me a chart of sentiment for ChatGPT GPT-5")
    print("\nType 'exit' to quit.\n")
    
    # Check for API keys
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found in environment.")
        print("Please set your Google API key in a .env file or environment variable.")
        return

    runner = InMemoryRunner(coordinator_agent, app_name="youtube_chatbot")
    session = await runner.session_service.create_session(app_name="youtube_chatbot", user_id="user_1")
    
    print("Chatbot ready!\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
        except EOFError:
            break
            
        if not user_input:
            continue
            
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break
            
        message = types.Content(role='user', parts=[types.Part(text=user_input)])
        
        try:
            print("\nBot: ", end="", flush=True)
            
            final_response = None
            async for event in runner.run_async(user_id="user_1", session_id=session.id, new_message=message):
                # Look for the final response from the coordinator
                if hasattr(event, 'is_final_response') and event.is_final_response():
                    if event.content and event.content.parts:
                        final_response = event.content.parts[0].text
                    break
                # Fallback: check for model responses
                elif hasattr(event, 'content') and event.content and event.content.parts:
                    if getattr(event, 'author', '') == coordinator_agent.name:
                        final_response = event.content.parts[0].text
            
            if final_response:
                print(final_response)
            else:
                print("I couldn't generate a response. Please try rephrasing your question.")
            
            print()  # Add spacing after response

        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            print(f"\nAn error occurred: {e}")
            print("Please try again with a different query.\n")

if __name__ == "__main__":
    asyncio.run(main())
