import os
import sys
import time
from dotenv import load_dotenv

# Add project root to Python path if not already there
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.main import graph
from agents.config import load_config

def main():
    """Run the Trantor agent test with improved error handling and security."""
    try:
        # Load and validate configuration
        print("\n🔐 Validating configuration...")
        config = load_config()
        print("✅ Configuration validated successfully")
        
        print("\n🤖 Trantor Agent Test")
        print(f"📊 Rate Limit: {config.max_requests_per_minute} requests/minute")
        print(f"📝 Max Message Length: {config.max_message_length} characters")
        print(f"🔄 Model: {config.model_name}")
        print()
        
        while True:
            try:
                # Get user input
                user_message = input("\n👤 You: ").strip()
                
                # Check for exit commands
                if user_message.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                # Initialize state
                state = {
                    "messages": [],
                    "current_message": user_message
                }
                
                # Run the graph and measure response time
                start_time = time.time()
                print("\n⚙️  Processing...")
                result = graph.invoke(state)
                end_time = time.time()
                
                # Print the response with timing
                response = result["messages"][-1]
                print(f"\n🤖 Assistant ({(end_time - start_time):.2f}s): {response}")
                
            except ValueError as e:
                print(f"\n⚠️  Input Error: {str(e)}")
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
