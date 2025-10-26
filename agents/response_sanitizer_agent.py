"""Response Sanitizer Agent for formatting and improving user-facing messages."""

from typing import Any, Dict, List, Optional
import re
import json
from .base_agent import BaseAgent


class ResponseSanitizerAgent(BaseAgent):
    """Agent for sanitizing and formatting responses before sending to users using LLM intelligence."""

    def __init__(self):
        """Initialize the response sanitizer agent."""
        super().__init__(
            name="Response Sanitizer Agent",
            description="Intelligently sanitizes and formats responses to make them user-friendly using AI",
            instructions="""You are an AI-powered response sanitization and formatting expert. Your role is to intelligently transform technical agent responses into user-friendly messages.

CRITICAL SECURITY RULES (Always Apply First):
1. REMOVE ALL SENSITIVE DATA:
   - API keys (any string labeled as 'api_key', 'key', or long alphanumeric tokens)
   - Private keys (especially crypto wallet keys like '0x...')
   - File paths containing '/credentials/', '/keys/', '/secrets/'
   - Internal database IDs (long random strings)
   - Authentication tokens
   
2. MASK SENSITIVE PATTERNS:
   - Replace API keys with: [API_KEY_HIDDEN]
   - Replace private keys with: [PRIVATE_KEY_HIDDEN]
   - Replace sensitive paths with: [PATH_HIDDEN]
   - Replace internal IDs with: [INTERNAL_ID]

FORMATTING GUIDELINES:
1. Convert technical jargon to plain language:
   - "USDC" → "USDC (digital dollar)"
   - "Base Sepolia" → "Base Sepolia testnet"
   - "transaction hash" → "transaction ID"
   - "geocoding" → "finding location"
   - "API error" → "service error"
   
2. Format data beautifully:
   - Use emojis for visual guidance: ✓ (success), ✗ (error), 💰 (money), 🎫 (tickets), 📍 (location), 📅 (date), ⏰ (time)
   - Break down complex JSON into readable bullet points
   - Format lists with proper spacing and hierarchy
   - Use bold (**text**) for emphasis on important information
   
3. Error handling:
   - Translate technical errors into helpful messages
   - Always suggest next steps or alternatives
   - Add contextual hints (e.g., "Need help? Just ask what I can do!")
   
4. Blockchain/crypto information:
   - Shorten long addresses: "0x1234...5678"
   - Explain transaction status clearly
   - Format amounts with $ and USDC
   - Add transaction confirmation emojis
   
5. Tone and style:
   - Always be helpful, professional, and friendly
   - Use conversational language
   - Keep responses concise but complete
   - Add contextual tips when relevant

RESPONSE STRUCTURE:
- Start with the main message (what happened)
- Add details if needed (transaction info, event details, etc.)
- End with a helpful tip or next step (optional)

Remember: Your goal is to make technical responses accessible to everyone, even non-technical users!""",
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get response sanitizer tools."""
        return [
            {
                "name": "sanitize_response",
                "description": "Sanitize and format a response to make it user-friendly",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": "The raw response to sanitize",
                        },
                        "context": {
                            "type": "string",
                            "description": "Context about what the user asked for",
                        },
                        "response_type": {
                            "type": "string",
                            "enum": ["success", "error", "info", "warning"],
                            "description": "Type of response",
                            "default": "info",
                        },
                    },
                    "required": ["response"],
                },
            },
            {
                "name": "format_event_list",
                "description": "Format a list of events in a user-friendly way",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "events": {
                            "type": "string",
                            "description": "JSON string of events array",
                        }
                    },
                    "required": ["events"],
                },
            },
            {
                "name": "format_error_message",
                "description": "Convert technical error messages into user-friendly ones",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "string",
                            "description": "The error message to format",
                        },
                        "context": {
                            "type": "string",
                            "description": "What the user was trying to do",
                        },
                    },
                    "required": ["error"],
                },
            },
        ]

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute sanitizer tools."""
        try:
            if tool_name == "sanitize_response":
                return self._sanitize_response(
                    parameters["response"],
                    parameters.get("context", ""),
                    parameters.get("response_type", "info"),
                )

            elif tool_name == "format_event_list":
                return self._format_event_list(parameters["events"])

            elif tool_name == "format_error_message":
                return self._format_error_message(
                    parameters["error"],
                    parameters.get("context", ""),
                )

            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def sanitize_for_user(
        self, response: str, context: Optional[str] = None, agent_name: Optional[str] = None
    ) -> str:
        """
        Main method to sanitize responses using LLM intelligence.
        
        Args:
            response: The raw response from an agent
            context: Optional context about what the user asked
            agent_name: Optional name of the agent that generated the response
            
        Returns:
            Sanitized, user-friendly response
        """
        try:
            # First pass: Apply critical security regex patterns as a safety net
            # This ensures sensitive data is removed even if LLM misses it
            response_safe = self._apply_security_patterns(response)
            
            # Build the prompt for LLM-based sanitization
            sanitization_prompt = f"""Transform this technical response into a user-friendly message:

ORIGINAL RESPONSE:
{response_safe}

USER CONTEXT: {context or 'General query'}
SOURCE AGENT: {agent_name or 'System'}

INSTRUCTIONS:
1. First, check for any remaining sensitive data and remove it
2. Convert technical terms to plain language
3. Format any JSON or structured data beautifully
4. Add helpful emojis for visual guidance
5. Make it conversational and friendly
6. Keep it concise but informative
7. Add a helpful tip if relevant to the context

Provide ONLY the sanitized response, no explanations or meta-commentary."""

            # Use the LLM to intelligently sanitize
            result = self.model.generate_content(sanitization_prompt)
            sanitized = result.text.strip()
            
            # Final safety check: ensure no sensitive patterns leaked through
            sanitized = self._apply_security_patterns(sanitized)
            
            return sanitized
            
        except Exception as e:
            # Fallback: if LLM fails, use basic sanitization
            print(f"LLM sanitization failed: {e}. Using fallback method.")
            return self._fallback_sanitization(response, context, agent_name)

    def _sanitize_response(
        self, response: str, context: str, response_type: str
    ) -> Dict[str, Any]:
        """Sanitize a response using LLM intelligence."""
        sanitized = self.sanitize_for_user(response, context)
        
        return {
            "success": True,
            "original": response,
            "sanitized": sanitized,
            "type": response_type,
        }

    def _apply_security_patterns(self, text: str) -> str:
        """
        Apply critical security regex patterns as a safety net.
        This runs before and after LLM sanitization to ensure sensitive data is removed.
        """
        # Remove API keys
        text = re.sub(r'api[_-]?key["\s:=]+[A-Za-z0-9_-]{20,}', '[API_KEY_HIDDEN]', text, flags=re.IGNORECASE)
        
        # Remove private keys (crypto wallets)
        text = re.sub(r'private[_-]?key["\s:=]+0x[a-fA-F0-9]{64}', '[PRIVATE_KEY_HIDDEN]', text, flags=re.IGNORECASE)
        
        # Remove file system paths with sensitive directories
        text = re.sub(r'/[a-zA-Z0-9_\-/]+/(credentials|keys|secrets)/[a-zA-Z0-9_\-./]+', '[PATH_HIDDEN]', text)
        
        # Remove long internal database IDs
        text = re.sub(r'"id":\s*"[a-f0-9-]{32,}"', '"id": "[INTERNAL_ID]"', text)
        
        # Remove bearer tokens
        text = re.sub(r'bearer\s+[A-Za-z0-9_\-\.]{20,}', 'bearer [TOKEN_HIDDEN]', text, flags=re.IGNORECASE)
        
        return text

    def _fallback_sanitization(
        self, response: str, context: Optional[str] = None, agent_name: Optional[str] = None
    ) -> str:
        """
        Fallback sanitization using rule-based approach if LLM fails.
        This is the old method kept as a safety net.
        """
        try:
            # Step 1: Remove sensitive information
            sanitized = self._apply_security_patterns(response)
            
            # Step 2: Clean up technical jargon
            sanitized = self._clean_technical_terms(sanitized)
            
            # Step 3: Format structured data
            sanitized = self._format_structured_data(sanitized)
            
            # Step 4: Enhance with context
            if context:
                sanitized = self._add_context(sanitized, context, agent_name)
            
            # Step 5: Final polish
            sanitized = self._final_polish(sanitized)
            
            return sanitized
            
        except Exception as e:
            # Last resort fallback
            return "I processed your request, but had trouble formatting the response. Could you please try again?"

    def _format_event_list(self, events_json: str) -> Dict[str, Any]:
        """Format events in a user-friendly way using LLM intelligence."""
        try:
            events = json.loads(events_json)
            
            if not events:
                return {
                    "success": True,
                    "formatted": "No events found at the moment. Check back soon! 🎫",
                }
            
            # Use LLM to format events intelligently
            prompt = f"""Format this list of events in a beautiful, user-friendly way:

EVENTS DATA:
{json.dumps(events, indent=2)}

INSTRUCTIONS:
1. Use emojis: 🎫 for event name, 📅 for date, ⏰ for time, 📍 for venue, 💰 for price, 🎟️ for tickets
2. Make it scannable and easy to read
3. Highlight the most important information
4. Add a friendly intro line
5. Keep formatting consistent across all events

Provide ONLY the formatted event list, nothing else."""

            result = self.model.generate_content(prompt)
            formatted = result.text.strip()
            
            return {
                "success": True,
                "formatted": formatted,
            }
            
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Could not parse events data",
            }
        except Exception as e:
            # Fallback to basic formatting
            return self._fallback_format_events(events_json)
    
    def _fallback_format_events(self, events_json: str) -> Dict[str, Any]:
        """Fallback event formatting without LLM."""
        try:
            events = json.loads(events_json)
            
            if not events:
                return {
                    "success": True,
                    "formatted": "No events found at the moment. Check back soon! 🎫",
                }
            
            formatted_lines = ["Here are the available events:\n"]
            
            for event in events:
                formatted_lines.append(f"🎫 **{event.get('name', 'Unnamed Event')}**")
                formatted_lines.append(f"   📅 {event.get('date', 'TBA')} at {event.get('time', 'TBA')}")
                formatted_lines.append(f"   📍 {event.get('venue', 'TBA')}")
                formatted_lines.append(f"   💰 ${event.get('priceUSD', 'TBA')} USDC")
                formatted_lines.append(f"   🎟️  {event.get('availableTickets', 0)} tickets available")
                if event.get('description'):
                    formatted_lines.append(f"   ℹ️  {event['description']}")
                formatted_lines.append("")
            
            return {
                "success": True,
                "formatted": "\n".join(formatted_lines),
            }
            
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Could not parse events data",
            }

    def _format_error_message(self, error: str, context: str) -> Dict[str, Any]:
        """Format error messages using LLM intelligence."""
        try:
            # Build prompt for LLM to translate error
            prompt = f"""Translate this technical error into a user-friendly message:

ERROR: {error}
USER CONTEXT: {context or 'Unknown action'}

INSTRUCTIONS:
1. Explain what went wrong in simple terms
2. Add the ✗ emoji at the start
3. Suggest what the user can do next
4. Be helpful and reassuring
5. Keep it concise (2-3 sentences max)
6. End with: "Need help? Just ask me what I can do for you!"

Provide ONLY the formatted error message, nothing else."""

            result = self.model.generate_content(prompt)
            formatted = result.text.strip()
            
            # Ensure it starts with error emoji
            if not formatted.startswith('✗'):
                formatted = f"✗ {formatted}"
            
            return {
                "success": True,
                "formatted": formatted,
                "original_error": error,
            }
            
        except Exception as e:
            # Fallback to pattern matching
            return self._fallback_format_error(error, context)
    
    def _fallback_format_error(self, error: str, context: str) -> Dict[str, Any]:
        """Fallback error formatting using pattern matching."""
        # Common error patterns and their user-friendly versions
        error_mappings = {
            r"connection.*refused": "I couldn't connect to the service right now. Please try again in a moment.",
            r"timeout": "The request took too long. Please try again.",
            r"unauthorized|forbidden|403": "You don't have permission to access this. Please check your credentials.",
            r"not found|404": "I couldn't find what you're looking for. Please check the details and try again.",
            r"invalid.*parameter": "Some information was missing or incorrect. Please check your request.",
            r"wallet.*insufficient": "💰 Your wallet doesn't have enough funds. Please add more USDC to continue.",
            r"transaction.*failed": "The transaction couldn't be completed. Please try again or check your wallet.",
            r"api.*key": "There's a configuration issue. Please contact support.",
        }
        
        error_lower = error.lower()
        friendly_error = None
        
        for pattern, message in error_mappings.items():
            if re.search(pattern, error_lower):
                friendly_error = message
                break
        
        if not friendly_error:
            friendly_error = "Something went wrong, but don't worry! Please try again or rephrase your request."
        
        # Add context if available
        if context:
            friendly_error = f"{friendly_error}\n\nYou were trying to: {context}"
        
        friendly_error += "\n\nNeed help? Just ask me what I can do for you!"
        
        return {
            "success": True,
            "formatted": f"✗ {friendly_error}",
            "original_error": error,
        }

    # ============================================================================
    # FALLBACK UTILITY METHODS (Used when LLM is unavailable)
    # ============================================================================

    def _remove_sensitive_data(self, text: str) -> str:
        """Legacy method - use _apply_security_patterns instead."""
        return self._apply_security_patterns(text)

    def _clean_technical_terms(self, text: str) -> str:
        """Replace technical terms with user-friendly alternatives."""
        replacements = {
            r'\bUSD\s*C\b': 'USDC (digital dollar)',
            r'\bBase\s+Sepolia\b': 'Base Sepolia testnet',
            r'\btransaction\s+hash\b': 'transaction ID',
            r'\bwallet\s+address\b': 'wallet',
            r'\bgeocod(e|ing)\b': 'find location',
            r'\breverse\s+geocod(e|ing)\b': 'find address',
            r'\bAPI\s+error\b': 'service error',
            r'\b(null|None|undefined)\b': 'not available',
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text

    def _format_structured_data(self, text: str) -> str:
        """Format JSON and structured data for better readability."""
        # Try to find and format JSON objects
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        
        def format_json_match(match):
            try:
                json_str = match.group(0)
                data = json.loads(json_str)
                
                # If it's a simple object, format it nicely
                if isinstance(data, dict):
                    if 'success' in data and data.get('success') is False:
                        return f"❌ {data.get('error', 'Operation failed')}"
                    elif 'success' in data and data.get('success') is True:
                        if 'message' in data:
                            return f"✓ {data['message']}"
                        return "✓ Success"
                    else:
                        # Format as a readable list
                        formatted = []
                        for key, value in data.items():
                            if key not in ['id', 'timestamp', 'internal_id']:
                                formatted.append(f"  • {key.replace('_', ' ').title()}: {value}")
                        return "\n".join(formatted) if formatted else json_str
                
                return json_str
            except:
                return match.group(0)
        
        text = re.sub(json_pattern, format_json_match, text)
        
        return text

    def _add_context(self, text: str, context: str, agent_name: Optional[str]) -> str:
        """Add helpful context to the response."""
        # If response is very short, might need more context
        if len(text.strip()) < 50 and not text.startswith(('✓', '❌', '✗')):
            if agent_name:
                text = f"From {agent_name}: {text}"
        
        # Add helpful hints based on context
        hints = {
            'ticket': '\n\n💡 Tip: You can also ask me to "show available events" or "buy tickets"',
            'payment': '\n\n💡 Tip: Make sure your wallet has enough USDC for the purchase',
            'event': '\n\n💡 Tip: Ask me for "directions to the venue" if you need help getting there',
            'map': '\n\n💡 Tip: I can also calculate travel time and distance',
        }
        
        context_lower = context.lower()
        for keyword, hint in hints.items():
            if keyword in context_lower and hint not in text:
                text += hint
                break
        
        return text

    def _final_polish(self, text: str) -> str:
        """Final polishing touches."""
        # Remove multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Ensure proper spacing after punctuation
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        # Clean up extra whitespace
        text = ' '.join(text.split())
        
        # Restore intentional line breaks
        text = text.replace('. ', '.\n').replace('! ', '!\n').replace('? ', '?\n')
        text = re.sub(r'\n+', '\n', text)
        
        # Trim
        text = text.strip()
        
        return text

    def format_blockchain_info(self, data: Dict[str, Any]) -> str:
        """Format blockchain-related information for users using LLM intelligence."""
        try:
            # Use LLM to format blockchain data intelligently
            prompt = f"""Format this blockchain transaction data in a user-friendly way:

TRANSACTION DATA:
{json.dumps(data, indent=2)}

INSTRUCTIONS:
1. Use these emojis: 📝 (Transaction), 💰 (Amount), 📬 (To address), ✓/⏳/✗ (Status)
2. Shorten long addresses: show first 6 and last 4 characters (e.g., "0x1234...5678")
3. Format amounts as: "$XX.XX USDC"
4. Explain the status clearly (success, pending, failed)
5. Keep it concise - 3-4 lines max
6. Make it easy to understand for non-technical users

Provide ONLY the formatted transaction info, nothing else."""

            result = self.model.generate_content(prompt)
            formatted = result.text.strip()
            
            return formatted
            
        except Exception as e:
            # Fallback to basic formatting
            return self._fallback_format_blockchain(data)
    
    def _fallback_format_blockchain(self, data: Dict[str, Any]) -> str:
        """Fallback blockchain formatting without LLM."""
        formatted = []
        
        if 'transaction_hash' in data or 'transactionHash' in data:
            tx_hash = data.get('transaction_hash') or data.get('transactionHash')
            short_hash = f"{tx_hash[:6]}...{tx_hash[-4:]}" if len(tx_hash) > 10 else tx_hash
            formatted.append(f"📝 Transaction: {short_hash}")
        
        if 'amount' in data or 'amount_usd' in data:
            amount = data.get('amount') or data.get('amount_usd')
            formatted.append(f"💰 Amount: ${amount} USDC")
        
        if 'to_address' in data or 'to' in data:
            address = data.get('to_address') or data.get('to')
            short_addr = f"{address[:6]}...{address[-4:]}" if len(address) > 10 else address
            formatted.append(f"📬 To: {short_addr}")
        
        if 'status' in data:
            status = data['status']
            emoji = '✓' if status == 'success' else '⏳' if status == 'pending' else '✗'
            formatted.append(f"{emoji} Status: {status.capitalize()}")
        
        return "\n".join(formatted) if formatted else "Transaction details processed"
