from typing import Optional
from pydantic import BaseModel, Field, validator
import os
from dotenv import load_dotenv

class AgentConfig(BaseModel):
    """Configuration for the agent system."""
    
    # Required API Keys
    openai_api_key: str = Field(..., min_length=20)
    langsmith_api_key: str = Field(..., min_length=20)
    
    # Optional API Keys
    anthropic_api_key: Optional[str] = Field(None, min_length=20)
    tavily_api_key: Optional[str] = Field(None, min_length=20)
    
    # Rate Limiting
    max_requests_per_minute: int = Field(default=60, ge=1, le=1000)
    max_tokens_per_request: int = Field(default=4000, ge=1, le=8000)
    max_message_length: int = Field(default=2000, ge=1, le=4000)
    
    # Model Configuration
    model_name: str = Field(default="gpt-3.5-turbo")
    temperature: float = Field(default=0.7, ge=0, le=2.0)
    
    @validator("openai_api_key")
    def validate_openai_key(cls, v):
        if not v.startswith(("sk-")):
            raise ValueError("Invalid OpenAI API key format")
        return v
    
    @validator("langsmith_api_key")
    def validate_langsmith_key(cls, v):
        if not v.startswith(("lsv2_")):
            raise ValueError("Invalid LangSmith API key format")
        return v
    
    @validator("anthropic_api_key")
    def validate_anthropic_key(cls, v):
        if v and not v.startswith(("sk-ant-")):
            raise ValueError("Invalid Anthropic API key format")
        return v
    
    @validator("tavily_api_key")
    def validate_tavily_key(cls, v):
        if v and not v.startswith(("tvly-")):
            raise ValueError("Invalid Tavily API key format")
        return v

def load_config() -> AgentConfig:
    """Load and validate configuration from environment variables."""
    load_dotenv()
    
    config_dict = {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "langsmith_api_key": os.getenv("LANGSMITH_API_KEY"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "tavily_api_key": os.getenv("TAVILY_API_KEY"),
    }
    
    try:
        return AgentConfig(**config_dict)
    except Exception as e:
        raise ValueError(f"Configuration error: {str(e)}")
