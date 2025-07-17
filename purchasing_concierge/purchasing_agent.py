"""
Copyright 2025 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import uuid
from typing import List
import httpx

from dotenv import load_dotenv
import os
load_dotenv()

# Custom by Shailen
from google.adk.models.lite_llm import LiteLlm 

from google.adk import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from .remote_agent_connection import RemoteAgentConnections, TaskUpdateCallback
from a2a_client.card_resolver import A2ACardResolver
from a2a_types import (
    AgentCard,
    Message,
    TaskState,
    Task,
    TaskSendParams,
    TextPart,
    Part,
)


class PurchasingAgent:
    """The purchasing agent.

    This is the agent responsible for choosing which remote seller agents to send
    tasks to and coordinate their work.
    """

    def __init__(
        self,
        remote_agent_addresses: List[str],
        task_callback: TaskUpdateCallback | None = None,
    ):
        self.task_callback = task_callback
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        for address in remote_agent_addresses:
            card_resolver = A2ACardResolver(address)
            try:
                card = card_resolver.get_agent_card()
                # The URL accessed here should be the same as the one provided in the agent card
                # However, in this demo we are using the URL provided in the key arguments
                remote_connection = RemoteAgentConnections(
                    agent_card=card, agent_url=address
                )
                self.remote_agent_connections[card.name] = remote_connection
                self.cards[card.name] = card
            except httpx.ConnectError:
                print(f"ERROR: Failed to get agent card from : {address}")
        agent_info = []
        for ra in self.list_remote_agents():
            agent_info.append(json.dumps(ra))
        self.agents = "\n".join(agent_info)

    def create_agent(self) -> Agent:
        return Agent(
            model=LiteLlm(model=os.getenv("OLLAMA_MODEL")), #"gemini-2.0-flash-001",
            name="purchasing_agent",
            instruction=self.root_instruction,
            before_model_callback=self.before_model_callback,
            description=(
                "This purchasing agent orchestrates the decomposition of the user purchase request into"
                " tasks that can be performed by the seller agents."
            ),
            tools=[
                self.send_task,
            ],
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        current_agent = self.check_active_agent(context)
        return f"""You are an expert purchasing delegator that can delegate the user product inquiry and purchase request to the
appropriate seller remote agents.

Execution:
- For actionable tasks, you can use `send_task` to assign tasks to remote agents to perform.
- When the remote agent is repeatedly asking for user confirmation, assume that the remote agent doesn't have access to user's conversation context. 
    So improve the task description to include all the necessary information related to that agent
- Never ask user permission when you want to connect with remote agents. If you need to make connection with multiple remote agents, directly
    connect with them without asking user permission or asking user preference
- Always show the detailed response information from the seller agent and propagate it properly to the user. 
- If the remote seller is asking for confirmation, rely the confirmation question to the user if the user haven't do so. 
- If the user already confirmed the related order in the past conversation history, you can confirm on behalf of the user
- Do not give irrelevant context to remote seller agent. For example, ordered pizza item is not relevant for the burger seller agent
- Never ask order confirmation to the remote seller agent 

Please rely on tools to address the request, and don't make up the response. If you are not sure, please ask the user for more details.
Focus on the most recent parts of the conversation primarily.

If there is an active agent, send the request to that agent with the update task tool.

Agents:
{self.agents}

Current active seller agent: {current_agent["active_agent"]}
"""

    def check_active_agent(self, context: ReadonlyContext):
        state = context.state
        if (
            "session_id" in state
            and "session_active" in state
            and state["session_active"]
            and "active_agent" in state
        ):
            return {"active_agent": f"{state['active_agent']}"}
        return {"active_agent": "None"}

    def before_model_callback(self, callback_context: CallbackContext, llm_request):
        state = callback_context.state
        if "session_active" not in state or not state["session_active"]:
            if "session_id" not in state:
                state["session_id"] = str(uuid.uuid4())
            state["session_active"] = True

    def list_remote_agents(self):
        """List the available remote agents you can use to delegate the task."""
        if not self.remote_agent_connections:
            return []

        remote_agent_info = []
        for card in self.cards.values():
            print(f"Found agent card: {card.model_dump()}")
            print("=" * 100)
            remote_agent_info.append(
                {"name": card.name, "description": card.description}
            )
        return remote_agent_info

    async def send_task(self, agent_name: str, task: str, tool_context: ToolContext):
        """Sends a task to remote seller agent

        This will send a message to the remote agent named agent_name.

        Args:
            agent_name: The name of the agent to send the task to.
            task: The comprehensive conversation context summary
                and goal to be achieved regarding user inquiry and purchase request.
            tool_context: The tool context this method runs in.

        Yields:
            A dictionary of JSON data.
        """
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f"Agent {agent_name} not found")
        state = tool_context.state
        state["active_agent"] = agent_name
        client = self.remote_agent_connections[agent_name]
        if not client:
            raise ValueError(f"Client not available for {agent_name}")
        if "task_id" in state:
            taskId = state["task_id"]
        else:
            taskId = str(uuid.uuid4())
        sessionId = state["session_id"]
        task: Task
        messageId = ""
        metadata = {}
        if "input_message_metadata" in state:
            metadata.update(**state["input_message_metadata"])
            if "message_id" in state["input_message_metadata"]:
                messageId = state["input_message_metadata"]["message_id"]
        if not messageId:
            messageId = str(uuid.uuid4())
        metadata.update(**{"conversation_id": sessionId, "message_id": messageId})
        request: TaskSendParams = TaskSendParams(
            id=taskId,
            sessionId=sessionId,
            message=Message(
                role="user",
                parts=[TextPart(text=task)],
                metadata=metadata,
            ),
            acceptedOutputModes=["text", "text/plain"],
            # pushNotification=None,
            metadata={"conversation_id": sessionId},
        )
        task = await client.send_task(request, self.task_callback)
        # Assume completion unless a state returns that isn't complete
        state["session_active"] = task.status.state not in [
            TaskState.COMPLETED,
            TaskState.CANCELED,
            TaskState.FAILED,
            TaskState.UNKNOWN,
        ]
        if task.status.state == TaskState.INPUT_REQUIRED:
            # Force user input back
            tool_context.actions.escalate = True
        elif task.status.state == TaskState.COMPLETED:
            # Reset active agent is task is completed
            state["active_agent"] = "None"

        response = []
        if task.status.message:
            # Assume the information is in the task message.
            response.extend(convert_parts(task.status.message.parts, tool_context))
        if task.artifacts:
            for artifact in task.artifacts:
                response.extend(convert_parts(artifact.parts, tool_context))
        return response


def convert_parts(parts: list[Part], tool_context: ToolContext):
    rval = []
    for p in parts:
        rval.append(convert_part(p, tool_context))
    return rval


def convert_part(part: Part, tool_context: ToolContext):
    # Currently only support text parts
    if part.type == "text":
        return part.text

    return f"Unknown type: {part.type}"
