from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot.agents.agent_manager import agent_manager

async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /usage command"""
    if not update.message or not update.effective_user:
        return

    agent = agent_manager.get_or_create_agent(update.effective_user.id)
    usage = agent.get_token_usage()
    
    usage_message = (
        f"🤖 Token Usage Statistics for {agent.identity.name}:\n\n"
        f"📊 Prompt tokens: {usage['prompt_tokens']:,}\n"
        f"📝 Completion tokens: {usage['completion_tokens']:,}\n"
        f"📈 Total tokens: {usage['total_tokens']:,}\n"
        f"💰 Remaining budget: {max(0, agent.token_budget - usage['total_tokens']):,}"
    )
    
    await update.message.reply_text(usage_message) 