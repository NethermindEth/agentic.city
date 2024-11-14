from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot.agents.agent_manager import agent_manager

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /start command"""
    if update.message is None or update.effective_user is None:
        return
        
    user = update.effective_user
    
    # Clear agent message history if it exists
    agent = agent_manager.get_or_create_agent(user.id)
    agent.clear_message_log()
    
    welcome_message = (
        f"Welcome {user.first_name}!\n\n"
        "I am an autonomous agent capable of extending my own capabilities through code. "
        "I can write, test, and deploy new features for myself, allowing me to adapt to your needs.\n\n"
        "Out of the box, I come with:\n"
        "- A dynamic persona system for adapting my personality and expertise\n"
        "- Long-term memory for maintaining context across conversations\n"
        "- Cryptocurrency and blockchain integration capabilities\n"
        "- Development tools for self-modification\n"
        "- Time awareness and scheduling capabilities\n\n"
        "But these are just starting points. If you need new functionality, just ask - "
        "I can write the code to implement it.\n\n"
        "Use /help to see available commands, or simply start chatting. \n\n"
        "What would you like to explore first?"
        "\n"
        "\n"
        "----------------------------------------\n"
        "DISCLAIMER: development tools not built yet :P\n"
        "DISCLAIMER: trusted execution platform not built yet\n"
        "DISCLAIMER: blockchain support rudimentary\n"
        "DISCLAIMER: EXPECT TO LOOSE ALL YOUR ASSETS\n"
        "DISCLAIMER: we will regularly reset the state of your agent\n"
        "----------------------------------------\n"
    )
    
    await update.message.reply_text(welcome_message)