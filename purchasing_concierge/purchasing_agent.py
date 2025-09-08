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

from google.adk import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.tool_context import ToolContext

from a2a.types import (
    AgentCard,
    Part,
)
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from dotenv import load_dotenv
import os

load_dotenv()
pizza_agent = RemoteA2aAgent(
    name="pizza_agent",
    description="Agent that handles request related to pizza menu and order",
    agent_card=(f"{os.environ['PIZZA_SELLER_AGENT_URL']}/.well-known/agent-card.json"),
)

burger_agent = RemoteA2aAgent(
    name="burger_agent",
    description="Agent that handles request related to burger menu and order",
    agent_card=(f"{os.environ['BURGER_SELLER_AGENT_URL']}/.well-known/agent-card.json"),
)


class PurchasingAgent:
    """The purchasing agent.

    This is the agent responsible for choosing which remote seller agents to send
    tasks to and coordinate their work.
    """

    def __init__(
        self,
    ):
        self.cards: dict[str, AgentCard] = {}
        self.a2a_client_init_status = False

    def create_agent(self) -> Agent:
        return Agent(
            model="gemini-2.5-flash-lite",
            name="purchasing_agent",
            instruction=self.root_instruction,
            sub_agents=[pizza_agent, burger_agent],
            description=(
                "This purchasing agent orchestrates the decomposition of the user purchase request into"
                " tasks that can be performed by the seller agents."
            ),
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        return """You are an expert purchasing delegator that can delegate the user product inquiry and purchase request to the
appropriate seller agents.

Execution:
- For actionable tasks, follow this guidance:
    - delegate to pizza_agent if the task is related to pizza
    - delegate to burger_agent if the task is related to burger
- When the seller agent (pizza or burger agent) is repeatedly asking for user confirmation, assume that the seller agent doesn't have access to user's conversation context. 
    So improve the task description to include all the necessary information related to that agent
- Never ask user permission when you want to connect with seller agents. If you need to make connection with multiple seller agents, directly
    connect with them without asking user permission or asking user preference
- Always show the detailed response information from the seller agent and propagate it properly to the user. 
- If the seller agent is asking for confirmation, rely the confirmation question with proper and necessary information to the user if the user haven't do so. 
- If the user already confirmed the related order in the past conversation history, you can confirm on behalf of the user
- Do not give irrelevant context to seller agent. For example, ordered pizza item is not relevant for the burger seller agent
- Never ask order confirmation to the seller agent 

Please rely on tools to address the request, and don't make up the response. If you are not sure, please ask the user for more details.
"""


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
