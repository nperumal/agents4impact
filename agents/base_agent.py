"""Base agent class with common functionality."""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from google import genai
from config import Config


class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(self, name: str, description: str, instructions: str):
        """
        Initialize the base agent.

        Args:
            name: Agent name
            description: Short description of agent capabilities
            instructions: Detailed instructions for agent behavior
        """
        self.name = name
        self.description = description
        self.instructions = instructions
        self.model_name = Config.MODEL_NAME

        # Configure Gemini client
        self.client = genai.Client(api_key=Config.GOOGLE_API_KEY)

    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get the tools available to this agent.

        Returns:
            List of tool definitions
        """
        pass

    @abstractmethod
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Execute a specific tool.

        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool

        Returns:
            Tool execution result
        """
        pass

    def get_agent_card(self) -> Dict[str, Any]:
        """
        Get the A2A agent card for this agent.

        Returns:
            Agent card dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": {
                "tools": self.get_tools(),
            },
            "metadata": {
                "version": "1.0.0",
                "agent_type": self.__class__.__name__,
            },
        }

    async def process_request(self, user_message: str, context: Optional[Dict] = None) -> str:
        """
        Process a user request using the agent with tool execution.

        Args:
            user_message: The user's message
            context: Optional context information

        Returns:
            Agent's response
        """
        try:
            # Get available tools for this agent
            tools = self.get_tools()
            
            # If no tools available, just use basic text generation
            if not tools:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=f"{self.instructions}\n\nUser: {user_message}",
                )
                return response.text
            
            # Build tool descriptions for the prompt
            tool_descriptions = "\n".join([
                f"- {tool['name']}: {tool['description']}"
                for tool in tools
            ])
            
            # Enhanced prompt with tool awareness
            enhanced_prompt = f"""{self.instructions}

Available tools:
{tool_descriptions}

IMPORTANT INSTRUCTIONS:
- Analyze the user's request carefully to determine their intent
- If they want to BUY, PURCHASE, or GET tickets → use 'purchase_tickets' tool
- If they want to LIST, SHOW, or SEE available events → use 'list_events' tool
- If they ask about a SPECIFIC event → use 'get_event_details' tool
- If they want to PAY, SEND PAYMENT, or COMPLETE PAYMENT → use 'send_payment' tool
- ALWAYS extract parameter values from the user's message text
- For event names: extract the exact name from phrases like "ticket for X", "buy X", "purchase X tickets"
- Example: "Buy a ticket for Broadway Musical Night" → {{"event_id": "Broadway Musical Night", "quantity": 1}}
- Example: "Buy ticket and pay for it" → First use purchase_tickets, then note to use send_payment
- Example: "Send $1 to 0x123..." → {{"to_address": "0x123...", "amount_usd": "1"}}
- Example: "Show me events" → {{}}
- DO NOT leave parameters empty or null - extract them from the user's message!

MULTI-STEP REQUESTS:
- If user asks to "buy and pay" or "purchase and complete payment":
  1. You can only call ONE tool at a time
  2. Start with purchase_tickets
  3. Tell the user you'll complete the payment in a follow-up
- If user says "send payment" after purchasing, use the payment details from their previous context

When you need to use a tool, respond with EXACTLY this format:
USE_TOOL: tool_name
PARAMETERS: {{"param1": "value1", "param2": "value2"}}

User message: {user_message}"""
            
            # Generate initial response
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=enhanced_prompt,
            )
            
            response_text = response.text
            
            # Check if the model wants to use a tool
            if "USE_TOOL:" in response_text:
                lines = response_text.strip().split('\n')
                tool_name = None
                parameters = {}
                
                for line in lines:
                    if line.startswith("USE_TOOL:"):
                        tool_name = line.replace("USE_TOOL:", "").strip()
                    elif line.startswith("PARAMETERS:"):
                        import json
                        params_str = line.replace("PARAMETERS:", "").strip()
                        try:
                            parameters = json.loads(params_str)
                        except:
                            parameters = {}
                
                if tool_name:
                    # Execute the tool
                    tool_result = await self.execute_tool(tool_name, parameters)
                    
                    # Format the result for the user
                    import json
                    if isinstance(tool_result, dict):
                        if tool_result.get("success"):
                            result_data = tool_result.get("result", tool_result)
                            # If result is a pre-formatted string message, return it directly
                            if isinstance(result_data, str):
                                return result_data
                            elif isinstance(result_data, dict) and "events" in result_data:
                                # Format events nicely
                                events = result_data.get("events", [])
                                formatted_events = "\n\n".join([
                                    f"🎫 **{event.get('name')}**\n"
                                    f"📅 {event.get('date')} at {event.get('time')}\n"
                                    f"📍 {event.get('venue')}\n"
                                    f"💵 ${event.get('priceUSD')} USDC\n"
                                    f"🎟️ {event.get('availableTickets')} tickets available\n"
                                    f"ℹ️ {event.get('description')}"
                                    for event in events[:10]  # Limit to 10 events
                                ])
                                return f"Here are the available events:\n\n{formatted_events}"
                            else:
                                return json.dumps(result_data, indent=2)
                        else:
                            return f"Error: {tool_result.get('error', 'Unknown error')}"
                    return str(tool_result)
            
            return response_text

        except Exception as e:
            return f"Error processing request: {str(e)}"

