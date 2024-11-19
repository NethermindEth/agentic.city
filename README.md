# Agentic.City 🌆

A monorepo housing experiments and implementations for the Agentic.City framework - a large-scale agent-based system with integrated crypto primitives and multi-platform distribution capabilities.

## Overview

Agentic.City aims to create a robust framework for autonomous agents that can:
- Interact with crypto primitives and blockchain technologies
- Distribute seamlessly across messaging platforms (Telegram, etc.)
- Enable complex agent-to-agent and agent-to-human interactions
- Scale effectively in decentralized environments

## Current Experiments 📚

| Experiment | Description | Status |
|------------|-------------|---------|
| swarmer | Modular framework for building intelligent agents with context-based architecture, dynamic tool creation, and state persistence | 🟢 Active |
| telegram-bot | Production-ready Telegram bot with command handling, rate limiting, and error handling | 🟡 In Progress |
| scripts | Utility scripts including Ollama wrapper and HTTP request helpers | 🟡 In Progress |

## Components

### Swarmer Framework 🤖

The core agent framework powering Agentic.City. Key features include:
- Context-based architecture for modular agent capabilities
- Dynamic tool creation and management
- Agent identity and state persistence
- Event handling and scheduling
- Secure crypto operations

[Learn more about Swarmer](./swarmer/README.md)

### Telegram Bot 🤖

## Deployment 🚀

The Telegram bot is automatically deployed to different environments based on branch merges:

- Production (main branch) -> prod environment
- Staging (staging branch) -> staging environment
- Development (develop branch) -> dev environment

Each environment has its own AWS EC2 instance and configuration. The deployment is handled automatically through GitHub Actions.

### Prerequisites for Deployment

- AWS EC2 instances set up for each environment
- Proper security groups and SSH access configured
- Environment variables set up in GitHub Secrets
- Appropriate AWS IAM roles and permissions