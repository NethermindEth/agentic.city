"""Module for inspecting and debugging agent state and behavior."""

import inspect
import logging
import os
import tempfile
from typing import Any, Optional

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.agents.agent_manager import agent_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_function_info(func: Any) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Get detailed information about a function through introspection.

    Returns (source_code, module_name, signature)
    """
    logger.info(
        f"Getting info for function: {func.__name__ if hasattr(func, '__name__') else 'unnamed'}"
    )

    # Get the original function if it's a tool
    if hasattr(func, "__original_func__"):
        func = func.__original_func__
    # Get the original function if wrapped
    elif hasattr(func, "__wrapped__"):
        func = func.__wrapped__

    try:
        # Get source code
        source = inspect.getsource(func)
    except (TypeError, OSError) as e:
        logger.info(f"Failed to get source: {str(e)}")
        source = None

    try:
        # Get module name
        module = inspect.getmodule(func)
        module_name = module.__name__ if module else None
    except Exception as e:
        logger.info(f"Failed to get module: {str(e)}")
        module_name = None

    try:
        # Get function signature
        signature = str(inspect.signature(func))
    except (TypeError, ValueError) as e:
        logger.info(f"Failed to get signature: {str(e)}")
        signature = None

    return source, module_name, signature


async def inspect_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inspect the current state of the agent and its contexts.

    Provides detailed information about the agent's memory, tools, and other contexts
    for debugging purposes.

    Args:
        update: The update containing the command
        context: The context for this handler
    """
    if not update.message or not update.effective_user:
        return

    if not context.args:
        await update.message.reply_text(
            "Please specify a tool name to inspect.\n" "Usage: /inspect <tool_name>"
        )
        return

    tool_name = context.args[0]
    logger.info(f"Inspecting tool: {tool_name}")

    agent = agent_manager.get_or_create_agent(update.effective_user.id)
    logger.info(f"Agent ID: {agent.identity.id}")

    # Check if tool exists
    if tool_name not in agent.tools:
        await update.message.reply_text(f"Tool '{tool_name}' not found.")
        return

    tool = agent.tools[tool_name]
    logger.info(f"Found tool object: {tool}")

    # Get tool information through introspection
    source, module_name, signature = get_function_info(tool)

    if not source and not module_name and not signature:
        await update.message.reply_text(
            f"Could not retrieve any information for tool '{tool_name}'. "
            "This might be a built-in tool with hidden implementation."
        )
        return

    # Build tool information message
    info_parts = []
    if module_name:
        info_parts.append(f"📦 Module: {module_name}")
    if signature:
        info_parts.append(f"✍️ Signature: {tool_name}{signature}")
    info_message = "\n".join(info_parts)

    # For longer source code, send as a file
    if source and len(source) > 100:
        logger.info("Sending source as file...")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            if info_message:
                temp_file.write(f"'''\n{info_message}\n'''\n\n")
            temp_file.write(source)
            temp_file.flush()

            await update.message.reply_document(
                document=open(temp_file.name, "rb"),
                filename=f"{tool_name}.py",
                caption=f"📝 Source code for tool '{tool_name}'",
            )

            # Clean up temp file
            os.unlink(temp_file.name)
    else:
        # For short snippets or when we only have metadata, send as text message
        try:
            message_parts = []
            if info_message:
                message_parts.append(info_message)
            if source:
                message_parts.append(f"📝 Source code:\n`{source.strip()}`")

            await update.message.reply_text(
                "\n\n".join(message_parts), parse_mode="MarkdownV2"
            )
        except Exception as e:
            logger.error(f"Failed to send formatted message: {e}")
            # If markdown parsing fails, send without formatting
            await update.message.reply_text("\n\n".join(message_parts))
