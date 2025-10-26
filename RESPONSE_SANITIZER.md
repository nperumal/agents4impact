# Response Sanitizer Agent - LLM-Powered Intelligence

## Overview

The **Response Sanitizer Agent** is an AI-powered agent that uses Google Gemini to intelligently transform technical responses into user-friendly messages. Unlike traditional rule-based sanitization, this agent understands context and meaning, making it much more effective and adaptive.

## Architecture

### LLM-Powered Approach

```
Raw Response → Security Patterns (Regex) → LLM Sanitization → Security Patterns (Regex) → User
                     ↓                            ↓                        ↓
              Remove obvious                 Intelligent             Final safety
              sensitive data                transformation            check
```

### Fallback System

If the LLM is unavailable, the agent automatically falls back to rule-based sanitization:

```
Raw Response → Rule-Based Sanitization → User
                     ↓
        • Regex patterns
        • Technical term replacement
        • Basic formatting
        • Context hints
```

## Key Features

### 1. **AI-Powered Intelligence**
- Uses Google Gemini 2.0 Flash for context-aware sanitization
- Understands meaning, not just patterns
- Adapts to different types of responses (success, error, info)
- Learns from context about what the user asked

### 2. **Security First**
- **Double-layer protection**: Regex patterns applied before AND after LLM
- Removes sensitive data:
  - API keys (`sk_live_...`, `api_key: ...`)
  - Private keys (`0xabcdef...64chars`)
  - File paths with sensitive directories (`/credentials/`, `/keys/`, `/secrets/`)
  - Bearer tokens
  - Internal database IDs

### 3. **User-Friendly Translation**
Automatically converts technical terms:
- `USDC` → `USDC (digital dollar)`
- `Base Sepolia` → `Base Sepolia testnet`
- `transaction hash` → `transaction ID`
- `geocoding` → `finding location`
- `API error` → `service error`

### 4. **Smart Formatting**
- Converts JSON to readable bullet points
- Uses emojis for visual guidance: ✓ ✗ 💰 🎫 📍 📅 ⏰
- Formats blockchain addresses: `0x1234...5678`
- Creates hierarchical, scannable layouts

### 5. **Error Intelligence**
Transforms technical errors into helpful messages:
- `ConnectionRefusedError` → "I couldn't connect to the service right now. Please try again in a moment."
- `TimeoutError` → "The request took too long. Please try again."
- `401/403` → "You don't have permission to access this. Please check your credentials."
- Always suggests next steps

## Usage

### Basic Usage

```python
from agents import ResponseSanitizerAgent

# Initialize the agent
sanitizer = ResponseSanitizerAgent()

# Sanitize a response
raw_response = """
Transaction completed successfully.
API Key: sk_live_abc123def456
Transaction hash: 0xabcd...1234
Amount: 50 USDC
"""

sanitized = sanitizer.sanitize_for_user(
    response=raw_response,
    context="User completed a ticket purchase",
    agent_name="Ticket Agent"
)

print(sanitized)
# Output: ✓ Your payment of $50 USDC was successful!
#         📝 Transaction: 0xabcd...1234
#         💡 Tip: Your tickets have been sent to your email.
```

### With Orchestrator Integration

The Response Sanitizer is integrated into the Orchestrator Agent:

```python
class OrchestratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(...)
        self.sanitizer = ResponseSanitizerAgent()
    
    async def process_request(self, user_message: str, context: Optional[Dict] = None) -> str:
        # Route to appropriate agent
        result = await self._route_to_agent("ticket", user_message)
        
        # Sanitize the response before returning to user
        sanitized = self.sanitizer.sanitize_for_user(
            response=result.get("response"),
            context=user_message,
            agent_name="Ticket Agent"
        )
        
        return sanitized
```

### Tool-Based Usage

The agent also provides tools for specific formatting tasks:

#### 1. Sanitize Response Tool
```python
result = await sanitizer.execute_tool(
    "sanitize_response",
    {
        "response": "Query executed with 42 rows returned",
        "context": "User queried the database",
        "response_type": "success"
    }
)
print(result["sanitized"])
```

#### 2. Format Event List Tool
```python
events_json = json.dumps([
    {"name": "Concert", "date": "2025-11-15", "priceUSD": "50"},
    {"name": "Theater", "date": "2025-11-20", "priceUSD": "35"}
])

result = await sanitizer.execute_tool(
    "format_event_list",
    {"events": events_json}
)
print(result["formatted"])
```

#### 3. Format Error Message Tool
```python
result = await sanitizer.execute_tool(
    "format_error_message",
    {
        "error": "Connection refused to localhost:8002",
        "context": "trying to buy tickets"
    }
)
print(result["formatted"])
```

#### 4. Format Blockchain Info
```python
tx_data = {
    "transactionHash": "0xabcd...1234",
    "to_address": "0x8626...1199",
    "amount_usd": "100.00",
    "status": "success"
}

formatted = sanitizer.format_blockchain_info(tx_data)
print(formatted)
# Output:
# 📝 Transaction: 0xabcd...1234
# 💰 Amount: $100.00 USDC
# 📬 To: 0x8626...1199
# ✓ Status: Success
```

## Testing

Run the comprehensive test suite:

```bash
# Activate virtual environment
source venv/bin/activate

# Run the test script
python test_sanitizer.py

# Run pytest tests
pytest tests/test_agents.py::TestResponseSanitizerAgent -v
```

## Configuration

The Response Sanitizer Agent uses the same configuration as other agents:

```env
# .env file
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_CLOUD_PROJECT=your_project_id
```

## Performance Considerations

### LLM Latency
- **Typical Response Time**: 1-3 seconds per sanitization
- **Optimization**: Use streaming for real-time applications
- **Fallback**: Instant response if LLM is unavailable

### Cost Optimization
- Uses Gemini 2.0 Flash (cost-effective model)
- Short prompts designed for efficiency
- Fallback to free rule-based approach when possible

### Error Handling
- Automatic fallback to rule-based sanitization
- Never blocks the user flow
- Graceful degradation

## Best Practices

### 1. Always Provide Context
```python
# Good ✓
sanitized = sanitizer.sanitize_for_user(
    response=raw_response,
    context="User purchased tickets",  # Provides context
    agent_name="Ticket Agent"
)

# Less effective ✗
sanitized = sanitizer.sanitize_for_user(response=raw_response)
```

### 2. Use Appropriate Response Types
```python
await sanitizer.execute_tool("sanitize_response", {
    "response": response,
    "response_type": "error"  # or "success", "info", "warning"
})
```

### 3. Trust the LLM
The LLM is smart enough to understand context. You don't need to pre-process:
```python
# Just pass raw response, LLM will handle it
sanitized = sanitizer.sanitize_for_user(complex_technical_response)
```

## Security Guarantees

### Multi-Layer Protection
1. **Pre-LLM Regex**: Removes obvious sensitive patterns
2. **LLM Intelligence**: Context-aware sanitization
3. **Post-LLM Regex**: Final safety check

### Sensitive Data Patterns
The agent protects against:
- ✓ API keys in any format
- ✓ Private keys (especially crypto wallets)
- ✓ Bearer tokens
- ✓ File system paths with credentials
- ✓ Internal IDs and UUIDs
- ✓ Email addresses (optional)

### Never Blocked
Even if sanitization fails completely, the system provides a safe fallback message rather than exposing raw data.

## Examples

See `test_sanitizer.py` for comprehensive examples:
- Sanitizing technical responses
- Formatting blockchain transactions
- Converting error messages
- Formatting event lists
- Handling JSON data

## Integration with Other Agents

The Response Sanitizer integrates seamlessly with all agents:

```python
# In Orchestrator Agent
response = await self._route_to_agent("ticket", user_message)
sanitized = self.sanitizer.sanitize_for_user(
    response=response["response"],
    context=user_message,
    agent_name="Ticket Agent"
)
return sanitized
```

## Troubleshooting

### LLM Not Working
If you see fallback messages:
1. Check `GOOGLE_API_KEY` is set correctly
2. Verify API quota isn't exceeded
3. Check network connectivity
4. Review logs for specific errors

### Unexpected Output
1. Provide more context in the `context` parameter
2. Specify the `agent_name` for better understanding
3. Try adjusting the `response_type`

### Performance Issues
1. Consider caching common responses
2. Use fallback mode for non-critical paths
3. Implement request batching for high volume

## Future Enhancements

- [ ] Response caching for common patterns
- [ ] Custom sanitization rules per agent
- [ ] Streaming support for real-time sanitization
- [ ] Multi-language support
- [ ] User preference learning
- [ ] A/B testing of LLM vs rule-based approaches

## Contributing

When improving the Response Sanitizer:
1. Always maintain the fallback system
2. Test with various response types
3. Ensure security patterns are comprehensive
4. Update tests for new features
5. Document any new behavior

## License

Part of the Agents4Impact multi-agent system.
