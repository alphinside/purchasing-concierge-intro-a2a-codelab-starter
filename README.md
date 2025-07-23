# Rough notes
uv run --with jupyter jupyter lab --port 9999




# Purchasing Concierge A2A Demo

> **⚠️ DISCLAIMER: THIS IS NOT AN OFFICIALLY SUPPORTED GOOGLE PRODUCT. THIS PROJECT IS INTENDED FOR DEMONSTRATION PURPOSES ONLY. IT IS NOT INTENDED FOR USE IN A PRODUCTION ENVIRONMENT.**

This demo shows how to enable A2A (Agent to Agent) protocol communication between purchasing concierge agent with the remote pizza and burger seller agents. Burger and Pizza seller agents is a independent agent that can be run on different server with different frameworks, in this demo example we, burger agent is built on top of Crew AI and pizza agent is built on top of LangGraph.

Detailed tutorial about this repo: [Getting Started with Agent-to-Agent (A2A) Protocol: A Purchasing Concierge and Remote Seller Agent Interactions with Gemini on Cloud Run](https://codelabs.developers.google.com/intro-a2a-purchasing-concierge?utm_campaign=CDR_0x6a71b73a_default_b415667894&utm_medium=external&utm_source=blog)

# Prerequisites

- If you are executing this project from your personal IDE, Login to Gcloud using CLI with the following command :

    ```shell
    gcloud auth application-default login
    ```

- Enable the following APIs

    ```shell
    gcloud services enable aiplatform.googleapis.com 
    ```

- Install [uv](https://docs.astral.sh/uv/getting-started/installation/) dependencies and prepare the python env

    ```shell
    curl -LsSf https://astral.sh/uv/install.sh | sh
    uv python install 3.12
    uv sync --frozen
    ```

# How to Run

First, we need to run the remote seller agents. We have two remote seller agents, one is burger agent and the other is pizza agent. We need to run them separately. These agents will serve the A2A Server

## Run the Burger Agent

1. Copy the `remote_seller_agents/burger_agent/.env.example` to `remote_seller_agents/burger_agent/.env`.
2. Fill in the required environment variables in the `.env` file. Substitute `GCLOUD_PROJECT_ID` with your Google Cloud Project ID.

    ```
    AUTH_USERNAME=burgeruser123
    AUTH_PASSWORD=burgerpass123
    GCLOUD_LOCATION=us-central1
    GCLOUD_PROJECT_ID={your-project-id}
    ```
3. Run the burger agent.

    ```bash
    cd remote_seller_agents/burger_agent
    uv sync --frozen
    uv run .
    ```
4. It will run on `http://localhost:10001`

## Run the Pizza Agent

1. Copy the `remote_seller_agents/pizza_agent/.env.example` to `remote_seller_agents/pizza_agent/.env`.
2. Fill in the required environment variables in the `.env` file. Substitute `GCLOUD_PROJECT_ID` with your Google Cloud Project ID.

    ```
    API_KEY=pizza123
    GCLOUD_LOCATION=us-central1
    GCLOUD_PROJECT_ID={your-project-id}
    ```
3. Run the pizza agent.

    ```bash
    cd remote_seller_agents/pizza_agent
    uv sync --frozen
    uv run .
    ```
4. It will run on `http://localhost:10000`

## Run the Purchasing Concierge Agent

Finally, we can run our A2A client capabilities owned by purchasing concierge agent.

1. Go back to demo root directory ( where `purchasing_concierge` directory is located )
2. Copy the `purchasing_concierge/.env.example` to `purchasing_concierge/.env`.
3. Fill in the required environment variables in the `.env` file. Substitute `GCLOUD_PROJECT_ID` with your Google Cloud Project ID.

    ```
    PIZZA_SELLER_AGENT_AUTH=pizza123
    PIZZA_SELLER_AGENT_URL=http://localhost:10000
    BURGER_SELLER_AGENT_AUTH=burgeruser123:burgerpass123
    BURGER_SELLER_AGENT_URL=http://localhost:10001
    GOOGLE_GENAI_USE_VERTEXAI=TRUE
    GOOGLE_CLOUD_PROJECT={your-project-id}
    GOOGLE_CLOUD_LOCATION=us-central1
    ```

3. Run the purchasing concierge agent with the UI

    ```bash
    uv sync --frozen
    uv run purchasing_concierge_demo.py
    ```

4. You should be able to access the UI at `http://localhost:8000`
    
    


