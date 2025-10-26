# Installation Guide - MCP Ticket Server

## Prerequisites

- **Node.js** >= 18.0.0
- **npm** >= 9.0.0
- TypeScript knowledge (helpful but not required)

## Quick Start

1. **Install Dependencies**
   ```bash
   cd mcp-ticket-server
   npm install
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (optional for mock mode)
   ```

3. **Build the Project**
   ```bash
   npm run build
   ```

4. **Run the Server**
   ```bash
   npm start
   ```

5. **Test with Inspector** (Optional)
   ```bash
   npm run inspector
   ```

## Development Setup

### 1. Install Development Tools

```bash
npm install
```

This installs all dependencies including:
- TypeScript compiler
- ESLint for code quality
- Prettier for code formatting
- MCP SDK
- Express for HTTP server
- Development utilities

### 2. IDE Setup

**VS Code** (Recommended):
- Install "ESLint" extension
- Install "Prettier" extension
- Install "TypeScript and JavaScript Language Features"

Create `.vscode/settings.json`:
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  }
}
```

### 3. Start Development

```bash
# Watch mode - automatically rebuilds on file changes
npm run watch

# Or use tsx for hot reload (recommended for development)
npm run dev
```

## Integration with Claude Desktop

### MacOS

1. Build the server:
   ```bash
   npm run build
   ```

2. Edit Claude config:
   ```bash
   code ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

3. Add configuration:
   ```json
   {
     "mcpServers": {
       "tickets": {
         "command": "node",
         "args": ["/Users/YOUR_USERNAME/workspace/agents4impact/mcp-ticket-server/build/index.js"]
       }
     }
   }
   ```

4. Restart Claude Desktop

### Windows

1. Build the server:
   ```bash
   npm run build
   ```

2. Edit Claude config:
   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```

3. Add configuration:
   ```json
   {
     "mcpServers": {
       "tickets": {
         "command": "node",
         "args": ["C:\\Users\\YOUR_USERNAME\\workspace\\agents4impact\\mcp-ticket-server\\build\\index.js"]
       }
     }
   }
   ```

4. Restart Claude Desktop

## Integration with Python Ticket Agent

The MCP server runs as a separate process and the Python Ticket Agent connects to it:

1. **Start the MCP Server**:
   ```bash
   cd mcp-ticket-server
   npm run dev
   ```

2. **Configure the Python Agent**:
   Edit `.env` in the root directory:
   ```env
   MCP_TICKET_SERVER_URL=http://localhost:3000
   ```

3. **Start the Python Agent**:
   ```bash
   cd ..
   source venv/bin/activate
   python -m uvicorn a2a_server:ticket_app --port 8002
   ```

## Troubleshooting

### Build Errors

```bash
# Clean and rebuild
npm run clean
npm run build
```

### Permission Issues

```bash
# Make sure the build output is executable
chmod +x build/index.js
```

### Module Not Found

```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### TypeScript Errors

```bash
# Check TypeScript version
npx tsc --version

# Rebuild with verbose output
npm run build -- --verbose
```

### Port Already in Use

```bash
# Find and kill the process using port 3000
lsof -ti:3000 | xargs kill -9

# Or change the port in .env
echo "PORT=3001" >> .env
```

### Connection Refused from Python Agent

1. Verify MCP server is running:
   ```bash
   curl http://localhost:3000/health
   ```

2. Check the MCP_TICKET_SERVER_URL in Python .env

3. Check firewall settings

## Verification

Test that everything works:

```bash
# 1. Build should complete without errors
npm run build

# 2. Server should start
npm start
# Should see: "MCP Ticket Server running on port 3000"

# 3. Test the health endpoint
curl http://localhost:3000/health
# Should return: {"status":"ok","server":"mcp-ticket-server"}

# 4. Inspector should open (if you have it installed)
npm run inspector
```

## Environment Variables

Create a `.env` file with these variables:

```bash
# Required
PORT=3000

# Optional (for production)
COINBASE_COMMERCE_API_KEY=your_api_key
PAYMENT_WALLET_PRIVATE_KEY=your_private_key
BASE_SEPOLIA_RPC_URL=your_rpc_url

# Development
USE_MOCK_PAYMENTS=true
NODE_ENV=development
```

## Next Steps

- Read the [README.md](README.md) for usage examples
- Check [../CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines
- Explore the source code in `src/`
- Test with the Python Ticket Agent

## Production Deployment

For production use:

1. **Set up environment variables**:
   ```bash
   # Use real API keys
   COINBASE_COMMERCE_API_KEY=real_key
   USE_MOCK_PAYMENTS=false
   NODE_ENV=production
   ```

2. **Build for production**:
   ```bash
   npm run build
   ```

3. **Use a process manager**:
   ```bash
   # PM2
   npm install -g pm2
   pm2 start build/index.js --name mcp-ticket-server
   
   # Or systemd
   sudo systemctl start mcp-ticket-server
   ```

4. **Set up monitoring**:
   - Application Performance Monitoring (APM)
   - Error tracking (Sentry, Rollbar)
   - Logging (Winston, Bunyan)

5. **Security**:
   - Use HTTPS
   - Enable rate limiting
   - Implement authentication
   - Validate all inputs
   - Use environment-specific configs

## Development Workflow

1. **Make changes** to TypeScript files in `src/`
2. **Run in watch mode**: `npm run dev`
3. **Lint code**: `npm run lint`
4. **Format code**: `npm run format`
5. **Test changes** with the Python agent or MCP inspector
6. **Build**: `npm run build`
7. **Commit** your changes

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the logs in the console
3. Search existing [GitHub issues](https://github.com/nperumal/agents4impact/issues)
4. Create a new issue with:
   - Error messages
   - Steps to reproduce
   - Environment details (OS, Node version, etc.)

## Useful Commands

```bash
# Development
npm run dev          # Hot reload development
npm run watch        # Watch and rebuild
npm run build        # Build TypeScript
npm start            # Run built server

# Code Quality
npm run lint         # Check code quality
npm run lint:fix     # Fix linting issues
npm run format       # Format code
npm run format:check # Check formatting

# Testing
npm run inspector    # Test with MCP inspector
npm test             # Run tests (when added)

# Maintenance
npm run clean        # Clean build directory
npm outdated         # Check for outdated packages
npm update           # Update packages
```

## Additional Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Express.js Guide](https://expressjs.com/en/guide/routing.html)
- [Coinbase Commerce API](https://commerce.coinbase.com/docs/)

---

Built with ❤️ using the Model Context Protocol (MCP)
