from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot.agents.basic import agent
import json
from typing import Any
from uuid import UUID

def serialize_object(obj: Any) -> Any:
    """Helper function to serialize objects"""
    if isinstance(obj, UUID):
        return str(obj)
    if hasattr(obj, '__dict__'):
        return {
            'type': obj.__class__.__name__,
            **{k: serialize_object(v) for k, v in obj.__dict__.items()}
        }
    elif isinstance(obj, dict):
        return {k: serialize_object(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_object(i) for i in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)

async def dump_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /dump command - dumps the entire agent state"""
    if update.message is None:
        return
        
    # Get agent state
    state = {
        "identity": serialize_object(agent.identity),
        "token_usage": agent.get_token_usage(),
        "token_budget": agent.token_budget,
        "model": agent.model,
        "contexts": {
            str(context_id): serialize_object(context)
            for context_id, context in agent.contexts.items()
        },
        "tools": {
            name: {
                "name": tool.__name__,
                "doc": tool.__doc__,
                "schema": tool.schema if hasattr(tool, 'schema') else None
            }
            for name, tool in agent.tools.items()
        },
    }
    
    # Format as pretty JSON
    dump_text = json.dumps(state, indent=2)
    
    # Split message if too long
    MAX_LENGTH = 2000  # Telegram message length limit
    if len(dump_text) > MAX_LENGTH:
        chunks = [dump_text[i:i + MAX_LENGTH] for i in range(0, len(dump_text), MAX_LENGTH)]
        for i, chunk in enumerate(chunks):
            prefix = "🤖 Agent State Dump (Part {}/{}):\n".format(i + 1, len(chunks))
            await update.message.reply_text(
                f"{prefix}```json\n{chunk}\n```",
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text(
            f"🤖 Agent State Dump:\n```json\n{dump_text}\n```",
            parse_mode='Markdown'
        ) 