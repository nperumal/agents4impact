# Google ADK A2A Multi-Agent System

A production-ready multi-agent system built with Google's Agent Development Kit (ADK) and Agent-to-Agent (A2A) protocol. This system provides a high-level orchestrator agent that coordinates three specialized remote agents: BigQuery, Ticket Management, and Maps Generation.

Force restart the web server with

```
cd /Users/kevinjones/google/mcp-ticket-server && pkill -f "tsx watch src/server.ts" && sleep 2 && npm run dev &
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ADK Web Interface                    │
│            (Mobile-First City Explorer)                 │
│                    Port: 5000                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Orchestrator Agent                     │
│              (High-Level Coordinator)                   │
│                    Port: 8000                           │
│                        │                                │
│    ┌───────────────────┴─────────────────┐             │
│    │                                     │             │
│    ▼                                     ▼             │
│ ┌────────────────────────┐   ┌─────────────────────┐  │
│ │ Response Sanitizer     │   │  Request Routing    │  │
│ │ (Security & UX)        │   │  Logic              │  │
│ └────────────────────────┘   └─────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┬─────────────┬─────────────┐
        │                         │             │             │
        ▼                         ▼             ▼             ▼
┌───────────────┐        ┌───────────────┐  ┌──────────────┐  ┌──────────────┐
│ BigQuery Agent│        │ Ticket Agent  │  │  Maps Agent  │  │ Search Agent │
│   Port: 8001  │        │  Port: 8002   │  │  Port: 8003  │  │  Port: 8004  │
└───────────────┘        └───────┬───────┘  └──────────────┘  └──────────────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │ MCP Ticket Server │
                       │ (Event Tickets +  │
                       │  USDC Payments)   │
                       │   Port: 3000      │
                       └───────────────────┘
```

## 🌟 Features

### 🌆 ADK Web Interface (City Explorer)

-   **Mobile-First Design**: Optimized for smartphones and tablets
-   **Chat Interface**: Natural language interaction with the multi-agent system
-   **Full-Screen Layout**: Uses 100% viewport width for maximum readability
-   **Admin Panel**: View real-time agent status and health checks
-   **Bottom Navigation**: Easy switching between Chat and Admin views
-   **Responsive**: Works perfectly on desktop, tablet, and mobile devices
-   **Modern UI**: Clean, gradient-based design with smooth animations

### Orchestrator Agent

-   Coordinates between specialized agents
-   Intelligently routes requests to appropriate agents
-   Keyword-based routing (ticket, payment, maps, data queries)
-   Aggregates and synthesizes multi-agent responses
-   **Integrated Response Sanitizer** for security and user experience
-   Provides unified interface for complex workflows

### 🛡️ Response Sanitizer Agent (LLM-Powered)

-   **AI-Powered Intelligence**: Uses Google Gemini to intelligently sanitize responses
-   **Context-Aware**: Understands meaning and context, not just pattern matching
-   **Security First**: Automatically removes sensitive data (API keys, private keys, file paths)
-   **User-Friendly Translation**: Converts technical jargon to plain language
-   **Smart Formatting**: Beautifies JSON and structured data for readability
-   **Error Intelligence**: Transforms technical errors into helpful, actionable messages
-   **Contextual Hints**: Adds relevant tips based on user actions and query context
-   **Blockchain Simplification**: Makes crypto transactions easy to understand
-   **Emoji Guidance**: Visual indicators for status (✓, ✗, 💰, 🎫, 📍)
-   **Consistent Tone**: Professional, friendly responses across all agents
-   **Fallback Safety**: Rule-based sanitization if LLM is unavailable
-   **Double Security**: Applies regex patterns before AND after LLM processing

### 🎫 Ticket Agent + MCP Server

**Ticket Agent (Port 8002):**
-   Natural language ticket purchasing
-   Fuzzy event name matching (handles typos!)
-   AI-powered payment completion with USDC
-   Wallet balance checking
-   Event browsing and discovery

**MCP Ticket Server (Port 3000):**
-   **Event Management**: List events, venues, and ticket inventory
-   **Blockchain Payments**: USDC payments on Base Sepolia testnet
-   **Payment Processing**: Create payment requests, verify transactions
-   **Wallet Integration**: Agent can send USDC payments automatically
-   **Express API**: RESTful endpoints for ticket operations
-   **Real-time Status**: Check payment status and ticket confirmation

**Example Event Types:**
- 🎵 Concerts (Rock Legends, Summer Music Festival)
- 🎭 Theater (Broadway Musical Night)
- 💼 Conferences (Tech Conference 2025)

**Pricing:** All tickets are $1 USDC for easy testing!

### BigQuery Agent

-   Execute SQL queries on BigQuery datasets
-   List datasets and tables
-   Get table schemas and metadata
-   Analyze query results with built-in intelligence
-   Query cost and performance monitoring

### Maps Agent

-   Geocode addresses to coordinates
-   Reverse geocode coordinates to addresses
-   Get directions between locations
-   Calculate distances and travel times
-   Find nearby places (mock implementation)
-   Generate static map URLs

### 🔍 Search Agent

-   **Web Search**: General web searches using Google Custom Search API
-   **Site-Specific Search**: Search within specific websites or domains
-   **News Search**: Find recent news articles with date filters
-   **Image Search**: Search for images with size and type filters
-   **Advanced Filters**: File type, exact phrases, exclusions, date ranges
-   **Language Support**: Multi-language search capabilities

## 📋 Prerequisites

-   **Python 3.10 or higher**
-   **Node.js 18+ and npm** (for MCP Ticket Server)
-   **Google Cloud Project** with:
    -   Gemini API enabled
    -   BigQuery API enabled (for BigQuery agent)
    -   Maps API enabled (for Maps agent, optional)
-   **Base Sepolia Testnet** (for blockchain payments):
    -   USDC tokens (from https://faucet.circle.com/)
    -   ETH for gas (from https://www.alchemy.com/faucets/base-sepolia)

## 🚀 Quick Start

### 1. Setup

Run the setup script:

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This will:

-   Create a Python virtual environment
-   Install all dependencies
-   Create a `.env` file from the template
-   Set up necessary directories

### 2. Authentication

**Recommended: Use Application Default Credentials (no service account key needed!)**

```bash
# Install gcloud SDK (if not already installed)
brew install google-cloud-sdk

# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login
```

Then edit `.env` file:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_API_KEY=your-gemini-api-key
# GOOGLE_APPLICATION_CREDENTIALS not needed with ADC!
```

**Note**: If your organization blocks service account keys, see [AUTHENTICATION.md](AUTHENTICATION.md) for detailed setup.

For getting your API keys, see [GET_CREDENTIALS.md](GET_CREDENTIALS.md)

### 3. Setup MCP Ticket Server

```bash
cd mcp-ticket-server
npm install
cd ..
```

Configure the blockchain wallet in `mcp-ticket-server/.env`:

```env
PAYMENT_WALLET_PRIVATE_KEY=your_private_key_here
BASE_SEPOLIA_RPC_URL=https://base-sepolia.g.alchemy.com/v2/your-api-key
```

> **Note:** See [WALLET_SETUP.md](WALLET_SETUP.md) for detailed wallet configuration.

### 4. Start All Services

**Start MCP Ticket Server:**
```bash
cd mcp-ticket-server && npm run dev &
```

**Start All ADK Agents:**
```bash
source venv/bin/activate
./scripts/start_all_agents.sh
```

**Start Web Interface:**
```bash
python web_server.py &
```

This starts all services:

-   🌐 **Web Interface**: http://localhost:5000
-   🎯 **Orchestrator**: http://localhost:8000
-   📊 **BigQuery Agent**: http://localhost:8001
-   🎫 **Ticket Agent**: http://localhost:8002
-   🗺️ **Maps Agent**: http://localhost:8003
-   🎟️ **MCP Ticket Server**: http://localhost:3000

### 5. Use the City Explorer

Open your browser to **http://localhost:5000**

**Try these queries in the chat:**
```
What events are available?
Buy a ticket for Rock Legends Concert
Send $1 USDC to <payment_address>
What's your USDC balance?
Get directions to Madison Square Garden
```

### 6. Test via API (Optional)

Run the example client:

```bash
python client_example.py
```

Or access the interactive API documentation:

-   http://localhost:8000/docs (Orchestrator)
-   http://localhost:8001/docs (BigQuery)
-   http://localhost:8002/docs (Ticket)
-   http://localhost:8003/docs (Maps)
-   http://localhost:3000/health (MCP Server)

### 7. Stop All Services

```bash
# Stop agents
./scripts/stop_all_agents.sh

# Stop MCP server
pkill -f "tsx watch src/server.ts"

# Stop web server
pkill -f "web_server.py"
```

## 💻 Usage Examples

### Using the City Explorer Web Interface

The City Explorer is a mobile-first web application for discovering events and exploring the city.

**Access:** http://localhost:5000

**Features:**
- 💬 **Chat View**: Natural language interaction with all agents
- ⚙️ **Admin View**: Real-time agent status monitoring

**Example Conversations:**

**Discover Events:**
```
User: What events are happening?
Agent: Here are the available events:
       🎫 Summer Music Festival 2025
       📅 2025-07-15 at 18:00
       📍 Hollywood Bowl
       💵 $1 USDC
       🎟️ 5000 tickets available
       ...
```

**Buy Tickets:**
```
User: I want to buy a ticket for Broadway Musical Night
Agent: 🎫 Ticket Reserved! USDC Payment Required
       
       💵 Payment Amount: $1.00 USDC
       📬 Send USDC to: 0x8af5...
       
       🤖 TO COMPLETE PAYMENT:
       Simply say: "Send $1 USDC to 0x8af5..."
```

**Complete Payment:**
```
User: Send $1 USDC to 0x8af5...
Agent: ✅ USDC Payment Sent Successfully!
       💵 Amount: $1 USDC
       🔗 Transaction: 0xabc123...
       🌐 View on Explorer: https://sepolia.basescan.org/tx/0xabc123...
```

**Check Balance:**
```
User: What's your USDC balance?
Agent: 💰 Agent Wallet Balance
       📬 Address: 0x9bDf...
       💵 USDC Balance: $10.00
       ⛽ ETH Balance: 0.05 ETH
```

### Using the MCP Ticket Server API

The MCP server provides REST endpoints for ticket operations:

**List Events:**
```bash
curl http://localhost:3000/mcp/tool/list_events \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Purchase Tickets:**
```bash
curl http://localhost:3000/mcp/tool/purchase_tickets \
  -H "Content-Type: application/json" \
  -d '{
    "eventId": "event-1",
    "quantity": 2,
    "customerEmail": "user@example.com",
    "customerName": "John Doe"
  }'
```

**Send Payment:**
```bash
curl http://localhost:3000/mcp/tool/send_payment \
  -H "Content-Type: application/json" \
  -d '{
    "toAddress": "0x8af52793B08843D1D0f4ee36964fCe986e667836",
    "amountUSD": "1.00"
  }'
```

**Check Wallet Balance:**
```bash
curl http://localhost:3000/mcp/tool/get_balance
```

### Using the Python Client

```python
from client_example import A2AClient
from config import Config

# Connect to orchestrator
orchestrator = A2AClient(f"http://localhost:{Config.ORCHESTRATOR_PORT}")

# Chat with the orchestrator
response = orchestrator.chat("What agents are available?")
print(response)

# Get agent card
card = orchestrator.get_agent_card()
print(f"Agent: {card['name']}")
print(f"Description: {card['description']}")

# Execute a tool directly
result = orchestrator.execute_tool("list_available_agents", {})
print(result)
```

### Using the REST API

#### Chat with an agent:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List available agents"}'
```

#### Execute a tool:

```bash
curl -X POST http://localhost:8001/execute-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "list_datasets",
    "parameters": {}
  }'
```

#### Create a ticket:

```bash
curl -X POST http://localhost:8002/execute-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "create_ticket",
    "parameters": {
      "title": "System issue",
      "description": "Database connection timeout",
      "category": "bug",
      "priority": "high"
    }
  }'
```

#### Geocode an address:

```bash
curl -X POST http://localhost:8003/execute-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "geocode",
    "parameters": {
      "address": "1600 Amphitheatre Parkway, Mountain View, CA"
    }
  }'
```

## 🛠️ Running Individual Agents

You can run agents individually for development or testing:

```bash
# Orchestrator only
python a2a_server.py --agent orchestrator

# BigQuery agent only
python a2a_server.py --agent bigquery

# Ticket agent only
python a2a_server.py --agent ticket

# Maps agent only
python a2a_server.py --agent maps

# Search agent only
python a2a_server.py --agent search

# Custom port
python a2a_server.py --agent orchestrator --port 9000
```

## 📁 Project Structure

```
google/
├── agents/                      # Agent implementations
│   ├── __init__.py
│   ├── base_agent.py           # Base agent class
│   ├── orchestrator.py         # Orchestrator agent
│   ├── bigquery_agent.py       # BigQuery agent
│   ├── ticket_agent.py         # Ticket management agent
│   ├── maps_agent.py           # Maps generation agent
│   └── search_agent.py         # Web search agent
├── scripts/                     # Utility scripts
│   ├── setup.sh                # Setup script
│   ├── start_all_agents.sh     # Start all agents
│   └── stop_all_agents.sh      # Stop all agents
├── logs/                        # Agent logs
├── a2a_server.py               # A2A server implementation
├── client_example.py           # Example client code
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Project metadata
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

| Variable                         | Description                         | Required |
| -------------------------------- | ----------------------------------- | -------- |
| `GOOGLE_CLOUD_PROJECT`           | Your Google Cloud project ID        | Yes      |
| `GOOGLE_API_KEY`                 | Gemini API key                      | Yes      |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON        | Yes      |
| `BIGQUERY_DATASET`               | Default BigQuery dataset            | No       |
| `BIGQUERY_LOCATION`              | BigQuery location (default: US)     | No       |
| `MAPS_API_KEY`                   | Google Maps API key                 | No       |
| `ORCHESTRATOR_PORT`              | Orchestrator port (default: 8000)   | No       |
| `BIGQUERY_AGENT_PORT`            | BigQuery agent port (default: 8001) | No       |
| `TICKET_AGENT_PORT`              | Ticket agent port (default: 8002)   | No       |
| `MAPS_AGENT_PORT`                | Maps agent port (default: 8003)     | No       |

## 🚢 Deployment

### Local Development

Use the provided scripts (see Quick Start section).

### Docker (Coming Soon)

Dockerfiles for containerized deployment will be added in future updates.

### Cloud Run / Kubernetes

Each agent can be deployed independently as a microservice:

1. Containerize each agent
2. Deploy to Cloud Run or Kubernetes
3. Update agent URLs in orchestrator configuration
4. Set up authentication between agents

### Production Considerations

1. **Security**:

    - Implement authentication between agents
    - Use HTTPS/TLS for all communications
    - Rotate API keys regularly
    - Use Secret Manager for sensitive data

2. **Monitoring**:

    - Set up Cloud Monitoring and Logging
    - Track agent health and performance
    - Monitor API usage and costs

3. **Scaling**:

    - Use load balancers for high availability
    - Implement horizontal scaling for agents
    - Cache frequent queries

4. **Error Handling**:
    - Implement retry logic
    - Add circuit breakers
    - Set up alerting for failures

## 🧪 Testing

To run tests (when implemented):

```bash
pytest tests/
```

## 📚 A2A Protocol

This project implements Google's Agent-to-Agent (A2A) protocol, which enables:

-   **Standardized Communication**: Agents communicate using a common protocol
-   **Agent Discovery**: Agents can discover each other's capabilities via agent cards
-   **Interoperability**: Works with agents from different frameworks and vendors
-   **Scalability**: Agents can be deployed and scaled independently

### Agent Card Structure

Each agent exposes an agent card at `/agent-card`:

```json
{
  "name": "Agent Name",
  "description": "Agent description",
  "capabilities": {
    "tools": [...]
  },
  "metadata": {
    "version": "1.0.0",
    "agent_type": "AgentClassName"
  }
}
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📄 License

This project is provided as-is for educational and development purposes.

## 🔗 Resources

-   [Google ADK Documentation](https://google.github.io/adk-docs/)
-   [A2A Protocol Specification](https://google.github.io/adk-docs/a2a/)
-   [Gemini API](https://ai.google.dev/)
-   [Google Cloud BigQuery](https://cloud.google.com/bigquery)
-   [Google Maps Platform](https://developers.google.com/maps)

## 💡 Next Steps

1. **Enhance Agent Intelligence**: Add more sophisticated reasoning and tool usage
2. **Add More Agents**: Create agents for other Google services (Cloud Storage, Vertex AI, etc.)
3. **Implement Authentication**: Add OAuth2 or JWT-based authentication
4. **Add Observability**: Implement distributed tracing and metrics
5. **Create UI**: Build a web interface for interacting with agents
6. **Add Tests**: Comprehensive unit and integration tests
7. **Docker Support**: Add Dockerfiles and docker-compose setup

## ⚠️ Notes

-   The Maps agent uses mock implementations by default. Configure `MAPS_API_KEY` for real API calls.
-   The Ticket agent uses in-memory storage. For production, integrate with a real ticketing system.
-   BigQuery queries have a 10GB billing limit by default for safety.
-   All agents use the `gemini-2.0-flash-exp` model by default.

## 🐛 Troubleshooting

### Agents won't start

-   Check that all environment variables are set correctly
-   Ensure ports 8000-8003 are not in use
-   Verify Google Cloud credentials are valid

### BigQuery errors

-   Ensure BigQuery API is enabled in your project
-   Verify service account has BigQuery permissions
-   Check dataset and table names are correct

### Connection errors

-   Ensure all agents are running
-   Check firewall settings
-   Verify port configurations

For more help, check the logs in the `logs/` directory.

---

Built with ❤️ using Google ADK and A2A Protocol
