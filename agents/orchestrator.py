"""Orchestrator agent for coordinating remote agents."""

from typing import Any, Dict, List, Optional
import requests
import google.genai as genai
from config import Config
from .base_agent import BaseAgent
from .response_sanitizer_agent import ResponseSanitizerAgent


class OrchestratorAgent(BaseAgent):
    """High-level orchestrator agent that coordinates remote agents."""

    def __init__(self):
        """Initialize the orchestrator agent."""
        super().__init__(
            name="Orchestrator Agent",
            description="High-level agent that coordinates BigQuery, Ticket, and Maps agents",
            instructions="""You are the main orchestrator agent. Your role is to:
1. Understand user requests and determine which specialized agents to use
2. Coordinate between multiple agents when tasks require multiple capabilities
3. Aggregate and synthesize results from different agents
4. Provide clear, helpful responses to users

Available specialized agents:
- BigQuery Agent: For data queries and analysis
- Ticket Agent: For EVENT TICKET SALES (concerts, shows, events, venues) with USDC blockchain payments
- Maps Agent: For geospatial data and map generation

When a user asks a question:
1. Determine which agent(s) can help
2. Formulate clear requests to those agents
3. Combine their responses into a coherent answer
4. Ask for clarification if the request is ambiguous

IMPORTANT: 
- Questions about "tickets for sale", "events", "concerts", "shows", "venues" → Route to Ticket Agent
- The Ticket Agent handles blockchain payments in USDC on Base Sepolia
- The Ticket Agent can list events, sell tickets, check payments, and manage wallet balance

Always provide helpful, accurate information and guide users to the appropriate resources.""",
        )

        # Initialize the response sanitizer
        self.sanitizer = ResponseSanitizerAgent()

        # Remote agent configurations
        self.remote_agents = {
            "bigquery": {
                "name": "BigQuery Agent",
                "url": f"http://localhost:{Config.BIGQUERY_AGENT_PORT}",
                "description": "Handles BigQuery data queries and analysis",
            },
            "ticket": {
                "name": "Ticket Agent",
                "url": f"http://localhost:{Config.TICKET_AGENT_PORT}",
                "description": "Sells event tickets (concerts, shows, venues) with USDC blockchain payments on Base Sepolia",
            },
            "maps": {
                "name": "Maps Agent",
                "url": f"http://localhost:{Config.MAPS_AGENT_PORT}",
                "description": "Provides geospatial information and maps",
            },
        }

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get orchestrator-specific tools."""
        return [
            {
                "name": "route_to_bigquery_agent",
                "description": "Route a request to the BigQuery agent for data queries and analysis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "request": {
                            "type": "string",
                            "description": "The request to send to the BigQuery agent",
                        }
                    },
                    "required": ["request"],
                },
            },
            {
                "name": "route_to_ticket_agent",
                "description": "Route a request to the Ticket agent for event ticket sales (concerts, shows, events, venues). Use this for: listing events, buying tickets, checking ticket availability, USDC payments",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "request": {
                            "type": "string",
                            "description": "The request to send to the Ticket agent (e.g., 'list available events', 'buy 2 tickets to concert', 'what shows are available?')",
                        }
                    },
                    "required": ["request"],
                },
            },
            {
                "name": "route_to_maps_agent",
                "description": "Route a request to the Maps agent for geospatial information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "request": {
                            "type": "string",
                            "description": "The request to send to the Maps agent",
                        }
                    },
                    "required": ["request"],
                },
            },
            {
                "name": "list_available_agents",
                "description": "List all available remote agents and their capabilities",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute orchestrator tools."""
        try:
            if tool_name == "route_to_bigquery_agent":
                return await self._route_to_agent("bigquery", parameters["request"])

            elif tool_name == "route_to_ticket_agent":
                return await self._route_to_agent("ticket", parameters["request"])

            elif tool_name == "route_to_maps_agent":
                return await self._route_to_agent("maps", parameters["request"])

            elif tool_name == "list_available_agents":
                return self._list_available_agents()

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            return {"error": str(e)}

    async def _route_to_agent(self, agent_key: str, request: str) -> Dict[str, Any]:
        """
        Route a request to a specific remote agent.

        Args:
            agent_key: The agent identifier (bigquery, ticket, or maps)
            request: The request to send to the agent

        Returns:
            Agent's response
        """
        import requests
        
        if agent_key not in self.remote_agents:
            return {"error": f"Unknown agent: {agent_key}"}

        agent_info = self.remote_agents[agent_key]

        try:
            # Make actual HTTP request to the agent
            response = requests.post(
                f"{agent_info['url']}/chat",
                json={"message": request},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "agent": agent_info["name"],
                "response": result.get("response", "No response from agent"),
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": f"Cannot connect to {agent_info['name']} at {agent_info['url']}. Make sure it's running.",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error routing to {agent_info['name']}: {str(e)}",
            }

    def _list_available_agents(self) -> Dict[str, Any]:
        """List all available remote agents."""
        return {
            "success": True,
            "agents": [
                {
                    "key": key,
                    "name": info["name"],
                    "url": info["url"],
                    "description": info["description"],
                }
                for key, info in self.remote_agents.items()
            ],
        }

    async def process_request(self, user_message: str, context: Optional[Dict] = None) -> str:
        """
        Process a user request with agent routing capabilities.

        Args:
            user_message: The user's message
            context: Optional context information

        Returns:
            Orchestrator's response (sanitized)
        """
        try:
            # Simple keyword-based routing for now
            # In production, use Gemini function calling
            message_lower = user_message.lower()
            
            # Check for ticket-related keywords (including payment keywords)
            ticket_keywords = ['ticket', 'event', 'concert', 'show', 'venue', 'buy', 'purchase', 'available', 'festival', 'performance', 'payment', 'pay', 'send', 'usdc', 'balance', 'wallet', 'complete', 'transaction', 'address', 'fund']
            if any(keyword in message_lower for keyword in ticket_keywords):
                result = await self._route_to_agent("ticket", user_message)
                if result.get("success"):
                    response = result.get("response", "No response from Ticket Agent")
                    # Sanitize the response before returning
                    return self.sanitizer.sanitize_for_user(
                        response, 
                        context=user_message,
                        agent_name="Ticket Agent"
                    )
                else:
                    error = result.get('error', 'Unknown error')
                    # Sanitize error messages too
                    return self.sanitizer.sanitize_for_user(
                        f"Error: {error}",
                        context=user_message,
                        agent_name="Ticket Agent"
                    )
            
            # Check for BigQuery keywords
            bigquery_keywords = ['query', 'data', 'bigquery', 'sql', 'database', 'table', 'analyze', 'dataset']
            if any(keyword in message_lower for keyword in bigquery_keywords):
                result = await self._route_to_agent("bigquery", user_message)
                if result.get("success"):
                    response = result.get("response", "No response from BigQuery Agent")
                    return self.sanitizer.sanitize_for_user(
                        response,
                        context=user_message,
                        agent_name="BigQuery Agent"
                    )
                else:
                    error = result.get('error', 'Unknown error')
                    return self.sanitizer.sanitize_for_user(
                        f"Error: {error}",
                        context=user_message,
                        agent_name="BigQuery Agent"
                    )
            
            # Check for Maps keywords
            maps_keywords = ['map', 'location', 'directions', 'geocode', 'address', 'navigation', 'route']
            if any(keyword in message_lower for keyword in maps_keywords):
                result = await self._route_to_agent("maps", user_message)
                if result.get("success"):
                    response = result.get("response", "No response from Maps Agent")
                    return self.sanitizer.sanitize_for_user(
                        response,
                        context=user_message,
                        agent_name="Maps Agent"
                    )
                else:
                    error = result.get('error', 'Unknown error')
                    return self.sanitizer.sanitize_for_user(
                        f"Error: {error}",
                        context=user_message,
                        agent_name="Maps Agent"
                    )
            
            # Default response if no clear routing
            agents_info = self._list_available_agents()
            agents_list = "\n".join([
                f"• {agent['name']}: {agent['description']}"
                for agent in agents_info['agents']
            ])
            
            default_response = f"""I can help you with 3 specialized agents:

{agents_list}

What would you like to do?"""
            
            return self.sanitizer.sanitize_for_user(
                default_response,
                context=user_message,
                agent_name="Orchestrator"
            )

        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            return self.sanitizer.sanitize_for_user(
                error_msg,
                context=user_message,
                agent_name="Orchestrator"
            )

