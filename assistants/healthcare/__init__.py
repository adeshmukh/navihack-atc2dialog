"""Healthcare assistant using Parlant framework."""

from chainlit_bootstrap.assistants import AssistantDescriptor
from .agent import handle_message

ASSISTANT_DESCRIPTOR = AssistantDescriptor(
    name="Healthcare Assistant",
    command="health",
    description="Helps patients schedule appointments and retrieve lab results",
    handle_message=handle_message,
)

