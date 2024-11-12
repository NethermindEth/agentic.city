from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot.agents.agent_manager import agent_manager

async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /tools command"""
    if not update.message or not update.effective_user:
        return

    # Check for verbose flag
    verbose = False
    if context.args and context.args[0].lower() in ['-v', '--verbose']:
        verbose = True

    agent = agent_manager.get_or_create_agent(update.effective_user.id)
    
    if not agent.tools:
        await update.message.reply_text("No tools available.")
        return

    if verbose:
        # Detailed view with descriptions and parameters
        message_parts = ["🛠 Available Tools:\n"]
        for name, tool in agent.tools.items():
            message_parts.append(f"\n📌 *{name}*")
            if tool.__doc__:
                # Clean up docstring and escape markdown
                doc = tool.__doc__.strip().split('\n')[0]  # First line only
                doc = doc.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[')
                message_parts.append(f"└ {doc}")
            
            if hasattr(tool, '__tool_schema__') and tool.__tool_schema__.get('parameters'):
                params = tool.__tool_schema__['parameters'].get('properties', {})
                if params:
                    message_parts.append("└ Parameters:")
                    for param_name, param_info in params.items():
                        if param_name != 'agent_identity':  # Skip internal parameter
                            param_type = param_info.get('type', 'any')
                            param_desc = param_info.get('description', '').replace('_', '\\_').replace('*', '\\*')
                            message_parts.append(f"  └ {param_name} ({param_type}): {param_desc}")
    else:
        # Simple list of tool names
        message_parts = ["🛠 Available Tools:"]
        for name in sorted(agent.tools.keys()):
            message_parts.append(f"└ {name}")

    # Join all parts and send
    message = '\n'.join(message_parts)
    
    try:
        await update.message.reply_text(
            message,
            parse_mode='MarkdownV2' if verbose else None
        )
    except Exception as e:
        # Fallback without markdown if parsing fails
        await update.message.reply_text(
            "Error formatting message. Try without verbose mode: /tools"
        ) 