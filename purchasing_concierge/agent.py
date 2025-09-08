from .purchasing_agent import PurchasingAgent
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

root_agent = PurchasingAgent().create_agent()
