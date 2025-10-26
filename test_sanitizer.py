#!/usr/bin/env python3
"""Test script for the LLM-powered Response Sanitizer Agent."""

import asyncio
from agents import ResponseSanitizerAgent


async def test_sanitizer():
    """Test various sanitization scenarios."""
    
    print("🧪 Testing LLM-Powered Response Sanitizer Agent\n")
    print("=" * 70)
    
    sanitizer = ResponseSanitizerAgent()
    
    # Test 1: Technical response with sensitive data
    print("\n📋 Test 1: Sanitizing technical response with API key")
    print("-" * 70)
    technical_response = """
    Connection successful to the database.
    API Key: ****************
    Query executed successfully.
    Results: 42 rows returned.
    """
    
    sanitized = sanitizer.sanitize_for_user(
        technical_response,
        context="User queried the database",
        agent_name="BigQuery Agent"
    )
    print(f"Original: {technical_response[:100]}...")
    print(f"\nSanitized:\n{sanitized}\n")
    
    # Test 2: Blockchain transaction
    print("\n📋 Test 2: Formatting blockchain transaction")
    print("-" * 70)
    blockchain_response = """
    Transaction hash: 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
    From: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb7
    To: 0x8626f6940e2eb28930efb4cef49b2d1f2c9c1199
    Amount: 50 USDC
    Gas used: 21000
    Status: confirmed
    """
    
    sanitized = sanitizer.sanitize_for_user(
        blockchain_response,
        context="User completed a payment",
        agent_name="Ticket Agent"
    )
    print(f"Original: {blockchain_response[:100]}...")
    print(f"\nSanitized:\n{sanitized}\n")
    
    # Test 3: Error message
    print("\n📋 Test 3: Formatting error message")
    print("-" * 70)
    result = await sanitizer.execute_tool(
        "format_error_message",
        {
            "error": "ConnectionRefusedError: [Errno 61] Connection refused to localhost:8002",
            "context": "trying to buy tickets",
        }
    )
    print(f"Original: ConnectionRefusedError...")
    print(f"\nSanitized:\n{result['formatted']}\n")
    
    # Test 4: Event list formatting
    print("\n📋 Test 4: Formatting event list")
    print("-" * 70)
    events_json = """[
        {
            "name": "Rock Concert",
            "date": "2025-11-15",
            "time": "8:00 PM",
            "venue": "Madison Square Garden",
            "priceUSD": "75",
            "availableTickets": 500,
            "description": "An epic night of rock music"
        },
        {
            "name": "Jazz Night",
            "date": "2025-11-20",
            "time": "7:30 PM",
            "venue": "Blue Note",
            "priceUSD": "45",
            "availableTickets": 50
        }
    ]"""
    
    result = await sanitizer.execute_tool(
        "format_event_list",
        {"events": events_json}
    )
    print(f"\nFormatted:\n{result['formatted']}\n")
    
    # Test 5: JSON data sanitization
    print("\n📋 Test 5: Sanitizing JSON response")
    print("-" * 70)
    json_response = """
    {
        "success": true,
        "data": {
            "user_id": "usr_abc123def456",
            "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb7",
            "balance": "150.50",
            "private_key": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "last_transaction": "2025-10-25T10:30:00Z"
        }
    }
    """
    
    sanitized = sanitizer.sanitize_for_user(
        json_response,
        context="User checked their wallet balance",
        agent_name="Ticket Agent"
    )
    print(f"Original: {json_response[:100]}...")
    print(f"\nSanitized:\n{sanitized}\n")
    
    # Test 6: Blockchain info formatting
    print("\n📋 Test 6: Formatting blockchain transaction details")
    print("-" * 70)
    tx_data = {
        "transactionHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "to_address": "0x8626f6940e2eb28930efb4cef49b2d1f2c9c1199",
        "amount_usd": "100.00",
        "status": "success"
    }
    
    formatted = sanitizer.format_blockchain_info(tx_data)
    print(f"\nFormatted:\n{formatted}\n")
    
    print("=" * 70)
    print("\n✅ All tests completed!")
    print("\n💡 Key Features Demonstrated:")
    print("   • LLM-powered intelligent sanitization")
    print("   • Automatic removal of sensitive data (API keys, private keys)")
    print("   • User-friendly formatting of technical responses")
    print("   • Beautiful emoji-enhanced output")
    print("   • Context-aware messaging")
    print("   • Fallback to rule-based sanitization if LLM fails")


if __name__ == "__main__":
    asyncio.run(test_sanitizer())
