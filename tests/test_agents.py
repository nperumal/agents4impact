"""Tests for agent functionality."""

import pytest
from agents import BigQueryAgent, TicketAgent, MapsAgent, OrchestratorAgent, ResponseSanitizerAgent


class TestBaseAgent:
    """Test base agent functionality."""

    def test_bigquery_agent_initialization(self):
        """Test BigQuery agent initializes correctly."""
        agent = BigQueryAgent()
        assert agent.name == "BigQuery Agent"
        assert "BigQuery" in agent.description

    def test_ticket_agent_initialization(self):
        """Test Ticket agent initializes correctly."""
        agent = TicketAgent()
        assert agent.name == "Ticket Agent"
        assert "ticket" in agent.description.lower()

    def test_maps_agent_initialization(self):
        """Test Maps agent initializes correctly."""
        agent = MapsAgent()
        assert agent.name == "Maps Agent"
        assert "map" in agent.description.lower()

    def test_orchestrator_agent_initialization(self):
        """Test Orchestrator agent initializes correctly."""
        agent = OrchestratorAgent()
        assert agent.name == "Orchestrator Agent"
        assert len(agent.remote_agents) == 3

    def test_response_sanitizer_agent_initialization(self):
        """Test Response Sanitizer agent initializes correctly."""
        agent = ResponseSanitizerAgent()
        assert agent.name == "Response Sanitizer Agent"
        assert "sanitiz" in agent.description.lower()


class TestAgentTools:
    """Test agent tool definitions."""

    def test_bigquery_tools(self):
        """Test BigQuery agent tools."""
        agent = BigQueryAgent()
        tools = agent.get_tools()
        assert len(tools) > 0
        tool_names = [tool["name"] for tool in tools]
        assert "execute_query" in tool_names
        assert "list_datasets" in tool_names

    def test_ticket_tools(self):
        """Test Ticket agent tools."""
        agent = TicketAgent()
        tools = agent.get_tools()
        assert len(tools) > 0
        tool_names = [tool["name"] for tool in tools]
        assert "create_ticket" in tool_names
        assert "update_ticket" in tool_names

    def test_maps_tools(self):
        """Test Maps agent tools."""
        agent = MapsAgent()
        tools = agent.get_tools()
        assert len(tools) > 0
        tool_names = [tool["name"] for tool in tools]
        assert "geocode" in tool_names
        assert "get_directions" in tool_names

    def test_orchestrator_tools(self):
        """Test Orchestrator agent tools."""
        agent = OrchestratorAgent()
        tools = agent.get_tools()
        assert len(tools) > 0
        tool_names = [tool["name"] for tool in tools]
        assert "list_available_agents" in tool_names

    def test_response_sanitizer_tools(self):
        """Test Response Sanitizer agent tools."""
        agent = ResponseSanitizerAgent()
        tools = agent.get_tools()
        assert len(tools) > 0
        tool_names = [tool["name"] for tool in tools]
        assert "sanitize_response" in tool_names
        assert "format_event_list" in tool_names
        assert "format_error_message" in tool_names


class TestAgentCards:
    """Test A2A agent cards."""

    def test_agent_card_structure(self):
        """Test agent card has correct structure."""
        agent = BigQueryAgent()
        card = agent.get_agent_card()
        
        assert "name" in card
        assert "description" in card
        assert "capabilities" in card
        assert "metadata" in card
        assert "tools" in card["capabilities"]


@pytest.mark.asyncio
class TestTicketAgent:
    """Test ticket agent operations."""

    async def test_create_ticket(self):
        """Test creating a ticket."""
        agent = TicketAgent()
        result = await agent.execute_tool(
            "create_ticket",
            {
                "title": "Test Ticket",
                "description": "Test description",
                "category": "bug",
                "priority": "high",
            },
        )
        
        assert result["success"] is True
        assert "ticket_id" in result
        assert result["ticket"]["title"] == "Test Ticket"
        assert result["ticket"]["status"] == "open"

    async def test_update_ticket(self):
        """Test updating a ticket."""
        agent = TicketAgent()
        
        # Create a ticket first
        create_result = await agent.execute_tool(
            "create_ticket",
            {
                "title": "Test Ticket",
                "description": "Test description",
                "category": "bug",
                "priority": "high",
            },
        )
        
        ticket_id = create_result["ticket_id"]
        
        # Update the ticket
        update_result = await agent.execute_tool(
            "update_ticket",
            {
                "ticket_id": ticket_id,
                "status": "in_progress",
                "note": "Working on it",
            },
        )
        
        assert update_result["success"] is True
        assert update_result["ticket"]["status"] == "in_progress"
        assert len(update_result["ticket"]["notes"]) == 1

    async def test_list_tickets(self):
        """Test listing all tickets."""
        agent = TicketAgent()
        
        # Create some tickets
        for i in range(3):
            await agent.execute_tool(
                "create_ticket",
                {
                    "title": f"Test Ticket {i}",
                    "description": f"Test description {i}",
                    "category": "bug",
                    "priority": "medium",
                },
            )
        
        # List all tickets
        result = await agent.execute_tool("list_all_tickets", {})
        
        assert result["success"] is True
        assert result["count"] >= 3


@pytest.mark.asyncio
class TestMapsAgent:
    """Test maps agent operations."""

    async def test_geocode(self):
        """Test geocoding an address."""
        agent = MapsAgent()
        result = await agent.execute_tool(
            "geocode",
            {"address": "1600 Amphitheatre Parkway, Mountain View, CA"},
        )
        
        assert result["success"] is True
        assert "location" in result
        assert "latitude" in result["location"]
        assert "longitude" in result["location"]

    async def test_generate_static_map(self):
        """Test generating a static map URL."""
        agent = MapsAgent()
        result = await agent.execute_tool(
            "generate_static_map",
            {
                "center": "San Francisco, CA",
                "zoom": 12,
                "size": "800x600",
            },
        )
        
        assert result["success"] is True
        assert "url" in result
        assert "maps.googleapis.com" in result["url"]


@pytest.mark.asyncio
class TestOrchestratorAgent:
    """Test orchestrator agent operations."""

    async def test_list_available_agents(self):
        """Test listing available agents."""
        agent = OrchestratorAgent()
        result = await agent.execute_tool("list_available_agents", {})
        
        assert result["success"] is True
        assert "agents" in result
        assert len(result["agents"]) == 3


@pytest.mark.asyncio
class TestResponseSanitizerAgent:
    """Test response sanitizer agent operations."""

    async def test_sanitize_response_basic(self):
        """Test basic response sanitization."""
        agent = ResponseSanitizerAgent()
        result = await agent.execute_tool(
            "sanitize_response",
            {
                "response": "The operation was successful with status code 200.",
                "context": "User asked about ticket purchase",
                "response_type": "success",
            },
        )
        
        assert result["success"] is True
        assert "sanitized" in result
        assert "original" in result

    async def test_remove_sensitive_data(self):
        """Test that sensitive data is removed."""
        agent = ResponseSanitizerAgent()
        
        # Test with API key
        response_with_key = "Your api_key is abc123xyz456789012345678901234567890"
        sanitized = agent.sanitize_for_user(response_with_key)
        assert "abc123xyz456789012345678901234567890" not in sanitized
        assert "[API_KEY_HIDDEN]" in sanitized
        
        # Test with private key
        response_with_private = "private_key: 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        sanitized = agent.sanitize_for_user(response_with_private)
        assert "0x1234567890abcdef" not in sanitized

    async def test_format_event_list(self):
        """Test formatting event lists."""
        agent = ResponseSanitizerAgent()
        events_json = """[
            {
                "name": "Broadway Show",
                "date": "2025-11-01",
                "time": "7:00 PM",
                "venue": "Broadway Theater",
                "priceUSD": "50",
                "availableTickets": 100,
                "description": "Amazing musical performance"
            },
            {
                "name": "Jazz Concert",
                "date": "2025-11-15",
                "time": "8:00 PM",
                "venue": "Jazz Club",
                "priceUSD": "35",
                "availableTickets": 50
            }
        ]"""
        
        result = await agent.execute_tool(
            "format_event_list",
            {"events": events_json},
        )
        
        assert result["success"] is True
        assert "formatted" in result
        formatted = result["formatted"]
        assert "Broadway Show" in formatted
        assert "Jazz Concert" in formatted
        assert "🎫" in formatted
        assert "💰" in formatted
        assert "$50 USDC" in formatted

    async def test_format_error_message(self):
        """Test formatting error messages."""
        agent = ResponseSanitizerAgent()
        
        # Test connection error
        result = await agent.execute_tool(
            "format_error_message",
            {
                "error": "Connection refused to localhost:8000",
                "context": "trying to connect to ticket service",
            },
        )
        
        assert result["success"] is True
        assert "formatted" in result
        assert "couldn't connect" in result["formatted"].lower()
        assert "✗" in result["formatted"]

    async def test_format_blockchain_info(self):
        """Test formatting blockchain information."""
        agent = ResponseSanitizerAgent()
        
        blockchain_data = {
            "transaction_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "amount_usd": "50.00",
            "to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb7",
            "status": "success",
        }
        
        formatted = agent.format_blockchain_info(blockchain_data)
        
        assert "Transaction:" in formatted
        assert "Amount:" in formatted
        assert "$50.00 USDC" in formatted
        assert "To:" in formatted
        assert "Status:" in formatted
        assert "✓" in formatted

    async def test_clean_technical_terms(self):
        """Test cleaning technical jargon."""
        agent = ResponseSanitizerAgent()
        
        technical_response = "Geocoding the address using reverse geocoding API"
        sanitized = agent.sanitize_for_user(technical_response)
        
        # Should replace technical terms with user-friendly ones
        assert "find location" in sanitized.lower() or "address" in sanitized.lower()

    async def test_sanitize_for_user_main_method(self):
        """Test the main sanitize_for_user method."""
        agent = ResponseSanitizerAgent()
        
        response = "Transaction completed with hash 0xabc123. Amount: 50 USDC"
        context = "User purchased a ticket"
        agent_name = "Ticket Agent"
        
        sanitized = agent.sanitize_for_user(response, context, agent_name)
        
        assert isinstance(sanitized, str)
        assert len(sanitized) > 0
        # Should not crash even with complex input

    async def test_empty_event_list(self):
        """Test handling empty event lists."""
        agent = ResponseSanitizerAgent()
        
        result = await agent.execute_tool(
            "format_event_list",
            {"events": "[]"},
        )
        
        assert result["success"] is True
        assert "No events found" in result["formatted"]

    async def test_malformed_json_handling(self):
        """Test handling malformed JSON gracefully."""
        agent = ResponseSanitizerAgent()
        
        result = await agent.execute_tool(
            "format_event_list",
            {"events": "not valid json{{{"},
        )
        
        assert result["success"] is False
        assert "error" in result

    async def test_error_pattern_matching(self):
        """Test various error pattern matching."""
        agent = ResponseSanitizerAgent()
        
        error_cases = [
            ("timeout error occurred", "took too long"),
            ("unauthorized access 403", "permission"),
            ("not found 404", "couldn't find"),
            ("wallet insufficient balance", "doesn't have enough funds"),
        ]
        
        for error, expected_phrase in error_cases:
            result = await agent.execute_tool(
                "format_error_message",
                {"error": error},
            )
            
            assert result["success"] is True
            assert expected_phrase in result["formatted"].lower()

