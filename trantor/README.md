# Trantor - Agent Management with LangGraph CLI

A powerful agent management system built using LangGraph CLI, enabling seamless orchestration and execution of AI agents in various modes.

## 📚 Getting Started with Windsurf

This project is designed to be used with Windsurf, the world's first agentic IDE. To get started:

1. Install Windsurf from [Windsurf Installation Guide](https://codeium.com/windsurf)
2. Follow the setup instructions to configure your development environment

## 🔗 Important Resources

### Documentation
- [LangChain Documentation](https://python.langchain.com/docs/tutorials/)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)

### Related Projects & Research
- [Nethermind](https://nethermind.io) - Pioneering Web3 Infrastructure
- [AI Agents Research and Applications](https://accelxr.substack.com/p/ai-agents-research-and-applications) - Deep dive into AI agents
- [Building AI Agents with LangGraph](https://mirror.xyz/jyu.eth/36lx6wKZqJPaVvj_X59Rdyh-zFul7mR6tTZm3-OO-_M) - Technical overview of LangGraph agent development

## 🚀 Features

- Agent orchestration and management
- Multiple execution modes:
  - In-memory execution
  - Docker containerization
  - CLI Platform integration
- Scalable architecture
- Easy-to-use interface
- LangSmith tracing and monitoring

## 📁 Project Structure

```
trantor/
├── agents/                 # Agent definitions and implementations
│   └── main.py            # Main agent graph implementation
├── .env                   # Environment variables
├── Dockerfile             # Container definition
├── LICENSE               # AGPL License
├── README.md             # This file
├── docker-compose.yml    # Docker services configuration
├── langgraph.json        # LangGraph configuration
├── setup.py              # Python package setup
└── smoke.py             # Test script for local development
```

## 🔑 API Keys and Environment Variables

Create a `.env` file in the project root with your API keys. You'll need to obtain these from:

1. **OpenAI API** (Required)
   - Sign up at: https://platform.openai.com/signup
   - Get API key from: https://platform.openai.com/api-keys
   - Used for: GPT-3.5/4 model access

2. **Anthropic API** (Optional)
   - Sign up at: https://console.anthropic.com/
   - Get API key from: https://console.anthropic.com/settings/keys
   - Used for: Claude model access

3. **Tavily API** (Optional)
   - Sign up at: https://tavily.com/
   - Get API key from: https://tavily.com/dashboard
   - Used for: Web search capabilities

4. **LangSmith** (Required)
   - Sign up at: https://smith.langchain.com/
   - Get API key from: https://smith.langchain.com/settings
   - Used for: Tracing and monitoring

Example `.env` file:
```env
# Required API Keys
OPENAI_API_KEY=sk-...            # Your OpenAI API key
LANGSMITH_API_KEY=lsv2-...       # Your LangSmith API key

# Optional API Keys
ANTHROPIC_API_KEY=sk-ant-...     # Your Anthropic API key (optional)
TAVILY_API_KEY=tvly-...          # Your Tavily API key (optional)

# Infrastructure Configuration (for Docker deployment)
# DATABASE_URI=postgresql://postgres:postgres@langgraph-postgres:5432/postgres
# REDIS_URI=redis://langgraph-redis:6379
```

### Security Notes
- Never commit your `.env` file to version control
- Rotate API keys regularly
- Use different API keys for development and production
- Consider using a secrets manager in production

## 🔧 Configuration

### Unified Configuration
The project uses a single configuration file `langgraph.json` that includes:
- Python version and dependencies
- Graph entry points
- Environment variables
- Development settings (port, hot reload, etc.)
- File exclusion patterns

## 📋 Prerequisites

- Python 3.12+ (earlier versions not tested)
- Docker (optional, for containerized execution)
- pip (Python package manager)

## 🛠️ Installation

### Windows

1. Install Python 3.12:
   - Download Python 3.12 from [python.org](https://www.python.org/downloads/)
   - Run the installer
   - ✅ Make sure to check "Add Python 3.12 to PATH" during installation
   - Verify installation:
     ```bash
     python --version
     ```

2. Install Git:
   - Download Git from [git-scm.com](https://git-scm.com/download/win)
   - Run the installer with default options
   - Verify installation:
     ```bash
     git --version
     ```

3. Set up SSH for GitHub:
   
   a. Generate Ed25519 SSH key:
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Press enter to save in default location
   # Enter a secure passphrase when prompted
   ```

   b. Start SSH agent and add your key:
   ```bash
   eval $(ssh-agent -s)
   ssh-add ~/.ssh/id_ed25519
   ```

   c. Copy your public key:
   ```bash
   cat ~/.ssh/id_ed25519.pub | clip
   ```

   d. Add SSH key to GitHub:
   1. Go to [GitHub Settings > SSH Keys](https://github.com/settings/keys)
   2. Click "New SSH key"
   3. Give it a meaningful title
   4. Paste your public key
   5. Click "Add SSH key"

   e. Authorize SSH key for Nethermind SSO:
   1. Go to [Nethermind's GitHub Organization](https://github.com/nethermindeth)
   2. Click on "Configure SSO" next to your newly added SSH key
   3. Click "Authorize" next to the Nethermind organization
   4. Complete the SSO authentication process if prompted

   f. Verify SSH connection:
   ```bash
   ssh -T git@github.com
   # You should see: "Hi username! You've successfully authenticated..."
   ```

4. Clone the repository:
   ```bash
   git clone git@github.com:nethermindeth/agentic.city.git
   cd agentic.city
   ```

5. Create and activate a virtual environment:
   ```bash
   # Navigate to trantor directory
   cd trantor
   
   # Create virtual environment (it will be automatically ignored by git)
   python -m venv .trantor
   .trantor\Scripts\activate
   ```
   Note: The `.trantor` virtual environment directory is automatically excluded from git via the `.gitignore` file. Keep it local and do not commit it to the repository.

6. Install required packages:
   ```bash
   python -m pip install --upgrade pip
   pip install -U "langgraph-cli[inmem]"
   pip install langchain
   pip install langchain-openai
   pip install langchain-community
   pip install pydantic
   ```

### Ubuntu

1. Update package list and install Python 3.12:
   ```bash
   sudo apt update
   sudo apt install software-properties-common
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt update
   sudo apt install python3.12 python3.12-venv python3.12-dev
   ```

2. Install Git:
   ```bash
   sudo apt install git
   ```

3. Set up SSH for GitHub:
   
   a. Generate Ed25519 SSH key:
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Press enter to save in default location
   # Enter a secure passphrase when prompted
   ```

   b. Start SSH agent and add your key:
   ```bash
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_ed25519
   ```

   c. Copy your public key:
   ```bash
   cat ~/.ssh/id_ed25519.pub | xclip -selection clipboard
   ```

   d. Add SSH key to GitHub:
   1. Go to [GitHub Settings > SSH Keys](https://github.com/settings/keys)
   2. Click "New SSH key"
   3. Give it a meaningful title
   4. Paste your public key
   5. Click "Add SSH key"

   e. Authorize SSH key for Nethermind SSO:
   1. Go to [Nethermind's GitHub Organization](https://github.com/nethermindeth)
   2. Click on "Configure SSO" next to your newly added SSH key
   3. Click "Authorize" next to the Nethermind organization
   4. Complete the SSO authentication process if prompted

   f. Verify SSH connection:
   ```bash
   ssh -T git@github.com
   # You should see: "Hi username! You've successfully authenticated..."
   ```

4. Clone the repository:
   ```bash
   git clone git@github.com:nethermindeth/agentic.city.git
   cd agentic.city
   ```

5. Create and activate a virtual environment:
   ```bash
   # Navigate to trantor directory
   cd trantor
   
   # Create virtual environment (it will be automatically ignored by git)
   python3.12 -m venv .trantor
   source .trantor/bin/activate
   ```
   Note: The `.trantor` virtual environment directory is automatically excluded from git via the `.gitignore` file. Keep it local and do not commit it to the repository.

6. Install required packages:
   ```bash
   python -m pip install --upgrade pip
   pip install -U "langgraph-cli[inmem]"
   pip install langchain
   pip install langchain-openai
   pip install langchain-community
   pip install pydantic
   ```

### Verify Installation

After installation, verify that everything is working:
```bash
langgraph --version
python -c "import langchain; print(langchain.__version__)"
```

## 🚀 Running the Project

After completing the installation steps above, navigate to the project directory:
```bash
cd trantor
```

### A. Running with Docker

The project includes Docker configuration for all required services:
- LangGraph API server
- PostgreSQL database
- Redis for real-time streaming

```bash
# Build the API server image
langgraph build --config langgraph.json -t trantor:latest

# Start all services
langgraph up
# or via docker-compose
# docker-compose up -d
```

Services will be available at:
- API: http://localhost:8123
- PostgreSQL: localhost:5433
- Redis: Internal network only

# Stop services
```bash
langgraph down
```


### B. Running in In-Memory Mode

```bash
langgraph dev --config configs/langgraph.json
```

This will start:
- 🚀 API: http://127.0.0.1:2024
- 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024 (I cannot make it run)
- 📚 API Docs: http://127.0.0.1:2024/docs

## 🔍 Using LangSmith Studio

LangSmith Studio provides powerful debugging and monitoring capabilities:

1. Open your web browser and navigate to https://smith.langchain.com/

2. The studio provides:
   - Real-time agent interaction visualization
   - Execution flow graphs
   - Agent state inspection
   - Message history
   - Performance metrics

3. Debug Features:
   - Click on any node to see agent details
   - View message payloads between agents
   - Inspect agent state changes
   - Monitor execution time and resource usage

4. Development Tools:
   - Live reload of agent changes
   - Interactive testing interface
   - Error tracking and logging
   - Performance profiling

## 🔄 Development Workflow

1. Make changes to agent definitions in the `agents/` directory
2. The development server will automatically reload changes
3. View updates in real-time on LangSmith Studio
4. Use the interactive console for testing:
```bash
langgraph console
```

## 🐛 Debugging Tips (not tested yet)

- Enable detailed logging:
```bash
langgraph dev --log-level debug
```

- Monitor specific agents:
```bash
langgraph viz --filter "agent_name"
```

- Export execution graphs:
```bash
langgraph export-trace
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the AGPL License (https://www.gnu.org/licenses/agpl-3.0.en.html) - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, please open an issue in the GitHub repository or contact the maintainers.