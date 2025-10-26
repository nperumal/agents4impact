# MCP Ticket Server - Quick Reference

## Installation
```bash
npm install
cp .env.example .env
npm run build
npm start
```

## Commands

| Command | Description |
|---------|-------------|
| `npm install` | Install dependencies |
| `npm run build` | Build TypeScript to JavaScript |
| `npm run dev` | Development mode with hot reload |
| `npm run watch` | Watch and rebuild on changes |
| `npm start` | Start the built server |
| `npm run inspector` | Test with MCP Inspector |
| `npm run lint` | Check code quality |
| `npm run lint:fix` | Fix linting issues |
| `npm run format` | Format code with Prettier |
| `npm run clean` | Remove build directory |

## Available Tools

### `list_events`
List all events with optional filtering.
```json
{
  "category": "concert",  // optional
  "city": "New York"      // optional
}
```

### `get_event`
Get detailed event information.
```json
{
  "eventId": "event-1"
}
```

### `list_venues`
List all venues.
```json
{
  "city": "Los Angeles"  // optional
}
```

### `purchase_tickets`
Purchase tickets for an event.
```json
{
  "eventId": "event-1",
  "quantity": 2,
  "customerEmail": "user@example.com",
  "customerName": "John Doe"
}
```

### `check_payment_status`
Check payment status.
```json
{
  "paymentIntentId": "pi_123"
}
```

### `confirm_payment`
Confirm a payment.
```json
{
  "paymentIntentId": "pi_123",
  "coinbaseChargeId": "charge_123"
}
```

### `get_my_tickets`
Get all tickets.
```json
{
  "status": "paid"  // optional: pending_payment, paid, cancelled, used
}
```

## Testing

### With curl
```bash
# Health check
curl http://localhost:3000/health

# List events
curl -X POST http://localhost:3000/mcp/tool/list_events \
  -H "Content-Type: application/json" \
  -d '{}'

# Purchase tickets
curl -X POST http://localhost:3000/mcp/tool/purchase_tickets \
  -H "Content-Type: application/json" \
  -d '{
    "eventId": "event-1",
    "quantity": 1,
    "customerEmail": "test@example.com",
    "customerName": "Test User"
  }'
```

### With MCP Inspector
```bash
npm run inspector
```

### With Python Agent
```bash
# Terminal 1: Start MCP Server
cd mcp-ticket-server
npm run dev

# Terminal 2: Start Python Agent
cd ..
source venv/bin/activate
python -m uvicorn a2a_server:ticket_app --port 8002
```

## Configuration

### .env file
```bash
PORT=3000
NODE_ENV=development
USE_MOCK_PAYMENTS=true
```

### Claude Desktop
```json
{
  "mcpServers": {
    "tickets": {
      "command": "node",
      "args": ["/full/path/to/mcp-ticket-server/build/index.js"]
    }
  }
}
```

## File Structure
```
src/
├── index.ts      # Entry point
├── server.ts     # Express + MCP server
├── data.ts       # Mock data
├── types.ts      # TypeScript types
└── blockchain.ts # Blockchain integration
```

## Common Issues

### Port in use
```bash
# Find and kill process
lsof -ti:3000 | xargs kill -9

# Or change port
echo "PORT=3001" >> .env
```

### Build fails
```bash
npm run clean
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Connection refused
```bash
# Check server is running
curl http://localhost:3000/health

# Check Python agent config
cat ../.env | grep MCP_TICKET_SERVER_URL
```

## Resources

- **Full Documentation**: [README.md](README.md)
- **Installation Guide**: [INSTALL.md](INSTALL.md)
- **MCP Protocol**: https://modelcontextprotocol.io/
- **Issues**: https://github.com/nperumal/agents4impact/issues

## Quick Tips

- 💡 Use `npm run dev` for development (auto-reload)
- 💡 Run `npm run lint:fix && npm run format` before committing
- 💡 Check logs in console for debugging
- 💡 Use MCP Inspector for testing tools
- 💡 Mock mode is enabled by default (no blockchain needed)
