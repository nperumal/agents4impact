"""A2A server implementation for exposing agents as A2A services."""

from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from agents import BigQueryAgent, TicketAgent, MapsAgent, OrchestratorAgent
from config import Config


# Request/Response models
class AgentRequest(BaseModel):
    """Request model for agent interactions."""

    message: str
    context: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Response model for agent interactions."""

    response: str
    agent_name: str
    success: bool = True


class ToolExecutionRequest(BaseModel):
    """Request model for tool execution."""

    tool_name: str
    parameters: Dict[str, Any]


# Create FastAPI apps for each agent
def create_agent_app(agent_class, agent_name: str) -> FastAPI:
    """
    Create a FastAPI application for an agent.

    Args:
        agent_class: The agent class to instantiate
        agent_name: Name of the agent for the API

    Returns:
        FastAPI application
    """
    app = FastAPI(title=f"{agent_name} A2A Service", version="1.0.0")

    # Add CORS middleware to allow web interface to connect
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify your web domain
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Instantiate the agent
    agent = agent_class()

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "service": agent_name,
            "version": "1.0.0",
            "protocol": "A2A",
            "status": "running",
        }

    @app.get("/agent-card")
    async def get_agent_card():
        """Get the A2A agent card."""
        return agent.get_agent_card()

    @app.post("/chat", response_model=AgentResponse)
    async def chat(request: AgentRequest):
        """
        Chat endpoint for interacting with the agent.

        Args:
            request: Agent request with message and optional context

        Returns:
            Agent response
        """
        try:
            response = await agent.process_request(request.message, request.context)
            return AgentResponse(
                response=response,
                agent_name=agent.name,
                success=True,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/execute-tool")
    async def execute_tool(request: ToolExecutionRequest):
        """
        Execute a specific tool on the agent.

        Args:
            request: Tool execution request

        Returns:
            Tool execution result
        """
        try:
            result = await agent.execute_tool(request.tool_name, request.parameters)
            return {"success": True, "result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/tools")
    async def get_tools():
        """Get available tools."""
        return {"tools": agent.get_tools()}

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "agent": agent.name}

    return app


# Create individual agent apps
bigquery_app = create_agent_app(BigQueryAgent, "BigQuery Agent")
ticket_app = create_agent_app(TicketAgent, "Ticket Agent")
maps_app = create_agent_app(MapsAgent, "Maps Agent")
orchestrator_app = create_agent_app(OrchestratorAgent, "Orchestrator Agent")


# Main entry point for running agents
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Run A2A agent server")
    parser.add_argument(
        "--agent",
        choices=["orchestrator", "bigquery", "ticket", "maps", "all"],
        default="orchestrator",
        help="Which agent to run",
    )
    parser.add_argument("--port", type=int, help="Port to run on (overrides config)")

    args = parser.parse_args()

    if args.agent == "all":
        print("Starting all agents in development mode...")
        print(f"Orchestrator: http://localhost:{Config.ORCHESTRATOR_PORT}")
        print(f"BigQuery Agent: http://localhost:{Config.BIGQUERY_AGENT_PORT}")
        print(f"Ticket Agent: http://localhost:{Config.TICKET_AGENT_PORT}")
        print(f"Maps Agent: http://localhost:{Config.MAPS_AGENT_PORT}")
        print("\nNote: In production, run each agent in a separate process/container")
        sys.exit(0)

    # Select agent and port
    agent_configs = {
        "orchestrator": (orchestrator_app, Config.ORCHESTRATOR_PORT),
        "bigquery": (bigquery_app, Config.BIGQUERY_AGENT_PORT),
        "ticket": (ticket_app, Config.TICKET_AGENT_PORT),
        "maps": (maps_app, Config.MAPS_AGENT_PORT),
    }

    app, default_port = agent_configs[args.agent]
    port = args.port if args.port else default_port

    print(f"Starting {args.agent} agent on port {port}")
    print(f"API docs available at http://localhost:{port}/docs")

    uvicorn.run(app, host="0.0.0.0", port=port)

