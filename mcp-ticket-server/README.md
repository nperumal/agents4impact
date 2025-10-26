# MCP Ticket Sales Server

Model Context Protocol (MCP) server for ticket management operations. This server provides tools for managing events, venues, and ticket purchasing with blockchain integration (USDC payments on Base Sepolia testnet).

## Features

-   🎫 **Event & Venue Management** - Browse and search events and venues
-   💳 **HTTP 402 Payment Flow** - Proper payment required responses
-   🪙 **Blockchain Integration** - USDC payments on Base Sepolia testnet
-   🔐 **MCP Protocol** - Standard Model Context Protocol implementation
-   ⚡ **Express Server** - HTTP/REST API endpoints
-   🔄 **Mock Mode** - Development mode with simulated payments
-   📊 **Real-time Data** - Mock data structure ready for production integration

## Quick Start

```bash
# Install dependencies
cd mcp-ticket-server
npm install

# Configure (optional for mock mode)
cp .env.example .env

# Build and run
npm run build
npm start
```

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

## Development

```bash
# Watch mode with auto-reload
npm run dev

# Build TypeScript
npm run build

# Watch and rebuild on changes
npm run watch

# Test with MCP Inspector
npm run inspector
```

## Available Tools

### `list_events`

List all available events with optional filtering

**Parameters:**

-   `category` (optional): Filter by event category
-   `city` (optional): Filter by city

### `get_event`

Get detailed information about a specific event

**Parameters:**

-   `eventId`: Event ID

### `list_venues`

List all available venues

**Parameters:**

-   `city` (optional): Filter by city

### `purchase_tickets`

Purchase tickets for an event (returns HTTP 402 for payment)

**Parameters:**

-   `eventId`: Event ID
-   `quantity`: Number of tickets (1-10)
-   `customerEmail`: Customer email
-   `customerName`: Customer name

**Response:**

-   Returns `requiresPayment: true` with `paymentUrl` for Coinbase Commerce
-   Ticket is created in `pending_payment` status

### `check_payment_status`

Check the status of a payment

**Parameters:**

-   `paymentIntentId`: Payment intent ID

### `confirm_payment`

Confirm a payment (simulates Coinbase webhook)

**Parameters:**

-   `paymentIntentId`: Payment intent ID
-   `coinbaseChargeId`: Coinbase charge ID

### `get_my_tickets`

Get all tickets

**Parameters:**

-   `status` (optional): Filter by ticket status

## Resources

-   `ticket://events` - All events listing
-   `ticket://venues` - All venues listing

## HTTP 402 Payment Flow

1. Client calls `purchase_tickets`
2. Server responds with `requiresPayment: true` and payment details
3. Payment information includes wallet address and USDC amount
4. User sends USDC payment on Base Sepolia testnet
5. System confirms payment and updates ticket status to `paid`
6. Client can retrieve ticket with QR code

## Project Structure

```
mcp-ticket-server/
├── src/
│   ├── index.ts          # Main server entry point
│   ├── server.ts         # Express server and MCP integration
│   ├── data.ts           # Mock data (events, venues, tickets)
│   ├── types.ts          # TypeScript type definitions
│   └── blockchain.ts     # Blockchain integration (optional)
├── build/                # Compiled JavaScript output
├── package.json          # NPM package configuration
├── tsconfig.json         # TypeScript configuration
├── .eslintrc.json        # ESLint configuration
├── .prettierrc           # Prettier configuration
├── .env.example          # Environment variables template
├── INSTALL.md           # Detailed installation guide
└── README.md            # This file
```

## Data Models

### Event
```typescript
{
  id: string;
  name: string;
  artist: string;
  date: string;
  time: string;
  venueId: string;
  category: string;
  priceUSD: number;
  availableTickets: number;
  description: string;
}
```

### Venue
```typescript
{
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  zipCode: string;
  capacity: number;
  type: "arena" | "club" | "outdoor";
  amenities: string[];
}
```

### Ticket
```typescript
{
  id: string;
  eventId: string;
  quantity: number;
  customerEmail: string;
  customerName: string;
  status: "pending_payment" | "paid" | "cancelled" | "used";
  paymentIntentId?: string;
  totalUSD: number;
  qrCode?: string;
}
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Server Configuration
PORT=3000
NODE_ENV=development

# Optional: Blockchain Integration
PAYMENT_WALLET_PRIVATE_KEY=your_wallet_private_key
BASE_SEPOLIA_RPC_URL=https://base-sepolia.g.alchemy.com/v2/your-api-key

# Development
USE_MOCK_PAYMENTS=true
```

### Claude Desktop Integration

**MacOS**: Edit `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: Edit `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "tickets": {
      "command": "node",
      "args": ["/absolute/path/to/agents4impact/mcp-ticket-server/build/index.js"]
    }
  }
}
```

## Integration with ADK Agent

The Python Ticket Agent connects to this MCP server via HTTP and exposes ticket sales functionality through the ADK A2A protocol.

**Architecture:**
```
User → Python Ticket Agent (Port 8002) → MCP Server (Port 3000) → Events/Payments
```

**Setup:**
1. Start MCP Server: `npm run dev` (Port 3000)
2. Configure Python Agent: `MCP_TICKET_SERVER_URL=http://localhost:3000`
3. Start Ticket Agent: `python -m uvicorn a2a_server:ticket_app --port 8002`

## Example Events

-   **Summer Music Festival 2025** - Hollywood Bowl - $150 USDC
-   **Tech Conference 2025** - Madison Square Garden - $299 USDC
-   **Rock Legends Concert** - The Fillmore - $75 USDC
-   **Broadway Musical Night** - Madison Square Garden - $120 USDC

## API Endpoints

### HTTP/REST Endpoints

```bash
# Health check
GET /health

# MCP tool execution
POST /mcp/tool/:toolName
```

### Example Usage

```bash
# List events
curl -X POST http://localhost:3000/mcp/tool/list_events \
  -H "Content-Type: application/json" \
  -d '{"category": "concert"}'

# Purchase tickets
curl -X POST http://localhost:3000/mcp/tool/purchase_tickets \
  -H "Content-Type: application/json" \
  -d '{
    "eventId": "event-1",
    "quantity": 2,
    "customerEmail": "user@example.com",
    "customerName": "John Doe"
  }'
```

## Development

### Code Quality

```bash
# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Check formatting
npm run format:check
```

### Testing

```bash
# Test with MCP Inspector
npm run inspector

# Test with curl
curl http://localhost:3000/health
```

### Building

```bash
# Clean build directory
npm run clean

# Build TypeScript
npm run build

# Build and make executable
npm run prepare
```

## Troubleshooting

### Server won't start
- Check if port 3000 is already in use: `lsof -i :3000`
- Try a different port: Edit `PORT` in `.env`

### Connection refused from Python agent
- Verify MCP server is running: `curl http://localhost:3000/health`
- Check `MCP_TICKET_SERVER_URL` in Python `.env`

### Build errors
```bash
npm run clean
rm -rf node_modules package-lock.json
npm install
npm run build
```

See [INSTALL.md](INSTALL.md) for more troubleshooting tips.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run linting and formatting: `npm run lint:fix && npm run format`
5. Build and test: `npm run build && npm start`
6. Submit a pull request

See [../CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

## Roadmap

- [ ] Real blockchain integration with Base Sepolia
- [ ] Database persistence (PostgreSQL/MongoDB)
- [ ] WebSocket support for real-time updates
- [ ] Payment confirmation webhooks
- [ ] QR code generation for tickets
- [ ] Email notifications
- [ ] Admin dashboard
- [ ] Analytics and reporting

## License

MIT

## Support

- **Issues**: https://github.com/nperumal/agents4impact/issues
- **Documentation**: See [INSTALL.md](INSTALL.md)
- **Main Project**: [Parent README](../README.md)

---

Built with ❤️ using the Model Context Protocol (MCP)
