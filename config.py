"""Configuration module for the multi-agent system."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration settings for the agent system."""

    # Google Cloud settings
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    # GOOGLE_APPLICATION_CREDENTIALS is optional - uses ADC if not set
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # BigQuery settings
    BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET")
    BIGQUERY_LOCATION = os.getenv("BIGQUERY_LOCATION", "US")

    # Agent urls and ports
    ORCHESTRATOR_URL = "https://orchestrator-568435446281.us-central1.run.app",
    BIGQUERY_URL = "https://bigquery-568435446281.us-central1.run.app",
    TICKET_URL = "https://ticket-568435446281.us-central1.run.app",
    MAPS_URL = "https://maps-568435446281.us-central1.run.app",

    ORCHESTRATOR_PORT = int(os.getenv("ORCHESTRATOR_PORT", 8000))
    BIGQUERY_AGENT_PORT = int(os.getenv("BIGQUERY_AGENT_PORT", 8001))
    TICKET_AGENT_PORT = int(os.getenv("TICKET_AGENT_PORT", 8002))
    MAPS_AGENT_PORT = int(os.getenv("MAPS_AGENT_PORT", 8003))

    # Ticketing system settings
    TICKET_SYSTEM_API_URL = os.getenv("TICKET_SYSTEM_API_URL")
    TICKET_SYSTEM_API_KEY = os.getenv("TICKET_SYSTEM_API_KEY")

    # Maps settings
    MAPS_API_KEY = os.getenv("MAPS_API_KEY")

    # MCP Ticket Server settings
    MCP_TICKET_SERVER_URL = os.getenv("MCP_TICKET_SERVER_URL", "http://localhost:3000")

    # Model settings
    MODEL_NAME = "gemini-2.0-flash-exp"

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        required_vars = [
            "GOOGLE_CLOUD_PROJECT",
            "GOOGLE_API_KEY",
        ]
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    print(f"Warning: {e}")
    print("Some features may not work correctly. Please check your .env file.")

