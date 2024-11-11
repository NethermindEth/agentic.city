from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot.agents.basic import agent

async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /usage command"""
    if update.message is None:
        return

    usage = agent.get_token_usage()
    
    usage_message = (
        f"🤖 Token Usage Statistics for {agent.identity.name}:\n\n"
        f"📊 Prompt tokens: {usage['prompt_tokens']:,}\n"
        f"📝 Completion tokens: {usage['completion_tokens']:,}\n"
        f"📈 Total tokens: {usage['total_tokens']:,}\n"
        f"💰 Remaining budget: {max(0, agent.token_budget - usage['total_tokens']):,}"
    )
    
    await update.message.reply_text(usage_message) 