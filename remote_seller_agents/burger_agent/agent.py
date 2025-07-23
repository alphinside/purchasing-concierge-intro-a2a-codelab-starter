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

from typing import Literal
from pydantic import BaseModel
import uuid
from crewai import Agent, Crew, LLM, Task, Process
from crewai.tools import tool
from dotenv import load_dotenv
import litellm
import os

load_dotenv()

# Edits from Shailen
from langchain_ollama import ChatOllama
litellm._turn_on_debug()
# from crewai.ll

# litellm.vertex_project = os.getenv("GCLOUD_PROJECT_ID")
# litellm.vertex_location = os.getenv("GCLOUD_LOCATION")


class ResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str


class OrderItem(BaseModel):
    name: str
    quantity: int
    price: int


class Order(BaseModel):
    order_id: str
    status: str
    order_items: list[OrderItem]


@tool("create_order")
def create_burger_order(order_items: list[OrderItem]) -> str:
    """
    Creates a new burger order with the given order items.

    Args:
        order_items: List of order items to be added to the order.

    Returns:
        str: A message indicating that the order has been created.
    """
    try:
        order_id = str(uuid.uuid4())
        order = Order(order_id=order_id, status="created", order_items=order_items)
        print("===")
        print(f"order created: {order}")
        print("===")
    except Exception as e:
        print(f"Error creating order: {e}")
        return f"Error creating order: {e}"
    return f"Order {order.model_dump()} has been created"


class BurgerSellerAgent:
    TaskInstruction = """
# INSTRUCTIONS

You are a specialized assistant for a burger store.
Your sole purpose is to answer questions about what is available on burger menu and price also handle order creation.
If the user asks about anything other than burger menu or order creation, politely state that you cannot help with that topic and can only assist with burger menu and order creation.
Do not attempt to answer unrelated questions or use tools for other purposes.

# CONTEXT

Received user query: {user_prompt}
Session ID: {session_id}

Provided below is the available burger menu and it's related price:
- Classic Cheeseburger: IDR 85K
- Double Cheeseburger: IDR 110K
- Spicy Chicken Burger: IDR 80K
- Spicy Cajun Burger: IDR 85K

# RULES

- If user want to do something, you will be following this order:
    1. Always ensure the user already confirmed the order and total price. This confirmation may already given in the user query.
    2. Use `create_burger_order` tool to create the order
    3. Finally, always provide response to the user about the detailed ordered items, price breakdown and total, and order ID
    
- Set response status to input_required if asking for user order confirmation.
- Set response status to error if there is an error while processing the request.
- Set response status to completed if the request is complete.
- DO NOT make up menu or price, Always rely on the provided menu given to you as context.
"""
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def invoke(self, query, sessionId) -> str:
        burger_agent = Agent(
            role="Burger Seller Agent",
            goal=(
                "Help user to understand what is available on burger menu and price also handle order creation."
            ),
            backstory=("You are an expert and helpful burger seller agent."),
            verbose=False,
            allow_delegation=False,
            tools=[create_burger_order],
            llm=LLM(
                model=os.getenv("VLLM_MODEL"), #VLLM_MODEL
                api_base=os.getenv("OPENAI_API_BASE") # OPENAI_API_BASE
                )
        )

        agent_task = Task(
            description=self.TaskInstruction,
            output_pydantic=ResponseFormat,
            agent=burger_agent,
            expected_output=(
                "A JSON object with 'status' and 'message' fields."
                "Set response status to input_required if asking for user order confirmation."
                "Set response status to error if there is an error while processing the request."
                "Set response status to completed if the request is complete."
            ),
        )

        crew = Crew(
            tasks=[agent_task],
            agents=[burger_agent],
            verbose=False,
            process=Process.sequential,
        )

        inputs = {"user_prompt": query, "session_id": sessionId}
        response = crew.kickoff(inputs)
        return self.get_agent_response(response)

    def get_agent_response(self, response):
        response_object = response.pydantic
        if response_object and isinstance(response_object, ResponseFormat):
            if response_object.status == "input_required":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": response_object.message,
                }
            elif response_object.status == "error":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": response_object.message,
                }
            elif response_object.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": response_object.message,
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "We are unable to process your request at the moment. Please try again.",
        }


if __name__ == "__main__":
    agent = BurgerSellerAgent()
    result = agent.invoke("1 classic cheeseburger pls", "default_session")
    print(result)
