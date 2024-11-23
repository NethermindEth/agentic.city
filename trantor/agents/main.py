from typing import Dict, TypedDict, List, Annotated
from langgraph.graph import Graph
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.tracers import LangChainTracer
import os
import sys
import time

# Add parent directory to Python path if not already there
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agents.config import AgentConfig, load_config

# Global rate limiting state
last_request_time = 0
request_count = 0

class AgentState(TypedDict):
    messages: List[str]
    current_message: str

def check_rate_limit(config_obj: AgentConfig):
    """Implement rate limiting."""
    global last_request_time, request_count
    
    current_time = time.time()
    time_window = 60  # 1 minute window
    
    # Reset counter if window has passed
    if current_time - last_request_time >= time_window:
        request_count = 0
        last_request_time = current_time
    
    # Check if we've exceeded rate limit
    if request_count >= config_obj.max_requests_per_minute:
        time_to_wait = time_window - (current_time - last_request_time)
        if time_to_wait > 0:
            raise ValueError(f"Rate limit exceeded. Please wait {time_to_wait:.1f} seconds.")
    
    request_count += 1

def validate_message(message: str, config_obj: AgentConfig) -> str:
    """Validate and sanitize input message."""
    if not message or not message.strip():
        raise ValueError("Message cannot be empty")
    
    message = message.strip()
    if len(message) > config_obj.max_message_length:
        raise ValueError(f"Message exceeds maximum length of {config_obj.max_message_length} characters")
    
    return message

def process_message(state: AgentState) -> AgentState:
    # Load and validate configuration
    config_obj = load_config()
    
    # Validate input
    state["current_message"] = validate_message(state["current_message"], config_obj)
    
    # Check rate limit
    check_rate_limit(config_obj)
    
    # Initialize tracer
    callback_manager = CallbackManager([LangChainTracer(
        project_name="trantor"
    )])
    
    # Initialize OpenAI chat model with tracing
    chat = ChatOpenAI(
        model=config_obj.model_name,
        temperature=config_obj.temperature,
        callback_manager=callback_manager,
        metadata={"agent_type": "chat"}
    )
    
    # Create a message from the current input
    messages = [HumanMessage(content=state["current_message"])]
    
    # Get response from OpenAI
    ai_message = chat.invoke(messages)
    
    # Add both messages to the history
    state["messages"].append(state["current_message"])
    state["messages"].append(ai_message.content)
    
    return state

def create_graph() -> Graph:
    # Create a graph with tracking
    workflow = Graph()

    # Add a node that processes messages
    workflow.add_node("process", process_message)

    # Create channels
    workflow.set_entry_point("process")
    workflow.set_finish_point("process")

    # Compile the graph
    return workflow.compile()

# Create the graph
graph = create_graph()
