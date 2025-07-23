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

from .purchasing_agent import PurchasingAgent
from dotenv import load_dotenv
import os

load_dotenv()

root_agent = PurchasingAgent(
    remote_agent_addresses=[
        # os.getenv("PIZZA_SELLER_AGENT_URL", "http://localhost:10000"),
        # os.getenv("BURGER_SELLER_AGENT_URL", "http://localhost:10001"),
    ]
).create_agent()
