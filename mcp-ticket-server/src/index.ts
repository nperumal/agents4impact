/**
 * MCP Ticket Sales Server with HTTP 402 Payment Support
 * Integrates with Coinbase Commerce for cryptocurrency payments
 */

import express from "express";
import cors from "cors";
import { v4 as uuidv4 } from "uuid";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
    ListResourcesRequestSchema,
    ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { events, venues, tickets, paymentIntents } from "./data.js";
import {
    Ticket,
    PaymentIntent,
    PaymentResponse,
} from "./types.js";

// Initialize Express server
const app = express();
app.use(cors());
app.use(express.json());

// Initialize MCP Server
const server = new Server(
    {
        name: "mcp-ticket-server",
        version: "1.0.0",
    },
    {
        capabilities: {
            tools: {},
            resources: {},
        },
    }
);

/**
 * Tool: List all available events
 */
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: "list_events",
                description: "List all available events with ticket information",
                inputSchema: {
                    type: "object" as const,
                    properties: {
                        category: {
                            type: "string",
                            enum: [
                                "concert",
                                "sports",
                                "theater",
                                "festival",
                                "conference",
                                "other",
                            ],
                        },
                        city: { type: "string" },
                    },
                },
            },
            {
                name: "get_event",
                description: "Get detailed information about a specific event",
                inputSchema: {
                    type: "object" as const,
                    properties: {
                        eventId: { type: "string" },
                    },
                    required: ["eventId"],
                },
            },
            {
                name: "list_venues",
                description: "List all available venues",
                inputSchema: {
                    type: "object" as const,
                    properties: {
                        city: { type: "string" },
                    },
                },
            },
            {
                name: "purchase_tickets",
                description:
                    "Purchase tickets for an event. Returns HTTP 402 if payment is required.",
                inputSchema: {
                    type: "object" as const,
                    properties: {
                        eventId: { type: "string" },
                        quantity: { type: "number", minimum: 1, maximum: 10 },
                        customerEmail: { type: "string", format: "email" },
                        customerName: { type: "string" },
                    },
                    required: [
                        "eventId",
                        "quantity",
                        "customerEmail",
                        "customerName",
                    ],
                },
            },
            {
                name: "check_payment_status",
                description: "Check the status of a payment",
                inputSchema: {
                    type: "object" as const,
                    properties: {
                        paymentIntentId: { type: "string" },
                    },
                    required: ["paymentIntentId"],
                },
            },
            {
                name: "confirm_payment",
                description: "Confirm a payment (simulates Coinbase webhook)",
                inputSchema: {
                    type: "object" as const,
                    properties: {
                        paymentIntentId: { type: "string" },
                        coinbaseChargeId: { type: "string" },
                    },
                    required: ["paymentIntentId", "coinbaseChargeId"],
                },
            },
            {
                name: "get_my_tickets",
                description: "Get all tickets (useful for testing)",
                inputSchema: {
                    type: "object" as const,
                    properties: {
                        status: {
                            type: "string",
                            enum: [
                                "pending_payment",
                                "paid",
                                "cancelled",
                                "used",
                            ],
                        },
                    },
                },
            },
        ],
    };
});

/**
 * Tool execution handler
 */
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    switch (name) {
        case "list_events": {
            let filteredEvents = Array.from(events.values());

            if (args?.category) {
                filteredEvents = filteredEvents.filter(
                    (e) => e.category === args.category
                );
            }

            if (args?.city) {
                filteredEvents = filteredEvents.filter((e) => {
                    const venue = venues.get(e.venueId);
                    return venue?.city
                        .toLowerCase()
                        .includes((args.city as string).toLowerCase());
                });
            }

            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify(
                            {
                                success: true,
                                count: filteredEvents.length,
                                events: filteredEvents,
                            },
                            null,
                            2
                        ),
                    },
                ],
            };
        }

        case "get_event": {
            const event = events.get(args?.eventId as string);

            if (!event) {
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                success: false,
                                error: "Event not found",
                            }),
                        },
                    ],
                };
            }

            const venue = venues.get(event.venueId);

            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify(
                            {
                                success: true,
                                event,
                                venue,
                            },
                            null,
                            2
                        ),
                    },
                ],
            };
        }

        case "list_venues": {
            let filteredVenues = Array.from(venues.values());

            if (args?.city) {
                filteredVenues = filteredVenues.filter((v) =>
                    v.city
                        .toLowerCase()
                        .includes((args.city as string).toLowerCase())
                );
            }

            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify(
                            {
                                success: true,
                                count: filteredVenues.length,
                                venues: filteredVenues,
                            },
                            null,
                            2
                        ),
                    },
                ],
            };
        }

        case "purchase_tickets": {
            const event = events.get(args?.eventId as string);

            if (!event) {
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                success: false,
                                requiresPayment: false,
                                error: "Event not found",
                            } as PaymentResponse),
                        },
                    ],
                };
            }

            const quantity = args?.quantity as number;
            if (event.availableTickets < quantity) {
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                success: false,
                                requiresPayment: false,
                                error: `Only ${event.availableTickets} tickets available`,
                            } as PaymentResponse),
                        },
                    ],
                };
            }

            const totalAmount = event.priceUSD * quantity;

            // Create ticket
            const ticketId = uuidv4();
            const ticket: Ticket = {
                id: ticketId,
                eventId: event.id,
                eventName: event.name,
                venue: event.venue,
                purchaseDate: new Date().toISOString(),
                eventDate: event.date,
                status: "pending_payment",
                priceUSD: totalAmount,
            };

            tickets.set(ticketId, ticket);

            // Create payment intent
            const paymentIntentId = uuidv4();
            const paymentIntent: PaymentIntent = {
                id: paymentIntentId,
                ticketId: ticketId,
                amount: totalAmount,
                currency: "USD",
                status: "pending",
                createdAt: new Date().toISOString(),
                expiresAt: new Date(
                    Date.now() + 30 * 60 * 1000
                ).toISOString(), // 30 minutes
            };

            // Simulate Coinbase Commerce integration
            const coinbaseChargeId = `charge_${uuidv4()}`;
            const paymentUrl = `https://commerce.coinbase.com/charges/${coinbaseChargeId}`;

            paymentIntent.coinbaseChargeId = coinbaseChargeId;
            paymentIntent.paymentUrl = paymentUrl;

            paymentIntents.set(paymentIntentId, paymentIntent);

            // Return HTTP 402 Payment Required response
            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify(
                            {
                                success: false,
                                requiresPayment: true,
                                paymentUrl: paymentUrl,
                                ticket: ticket,
                                paymentIntent: paymentIntent,
                            } as PaymentResponse,
                            null,
                            2
                        ),
                    },
                ],
            };
        }

        case "check_payment_status": {
            const paymentIntent = paymentIntents.get(
                args?.paymentIntentId as string
            );

            if (!paymentIntent) {
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                success: false,
                                error: "Payment intent not found",
                            }),
                        },
                    ],
                };
            }

            const ticket = tickets.get(paymentIntent.ticketId);

            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify(
                            {
                                success: true,
                                paymentIntent,
                                ticket,
                            },
                            null,
                            2
                        ),
                    },
                ],
            };
        }

        case "confirm_payment": {
            const paymentIntent = paymentIntents.get(
                args?.paymentIntentId as string
            );

            if (!paymentIntent) {
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                success: false,
                                error: "Payment intent not found",
                            }),
                        },
                    ],
                };
            }

            if (
                paymentIntent.coinbaseChargeId !==
                (args?.coinbaseChargeId as string)
            ) {
                return {
                    content: [
                        {
                            type: "text" as const,
                            text: JSON.stringify({
                                success: false,
                                error: "Invalid charge ID",
                            }),
                        },
                    ],
                };
            }

            // Update payment status
            paymentIntent.status = "completed";
            paymentIntents.set(args?.paymentIntentId as string, paymentIntent);

            // Update ticket status
            const ticket = tickets.get(paymentIntent.ticketId);
            if (ticket) {
                ticket.status = "paid";
                ticket.paymentId = paymentIntent.id;
                ticket.qrCode = `QR-${uuidv4()}`;
                tickets.set(ticket.id, ticket);

                // Update available tickets
                const event = events.get(ticket.eventId);
                if (event) {
                    event.availableTickets -= 1;
                    events.set(event.id, event);
                }
            }

            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify(
                            {
                                success: true,
                                message: "Payment confirmed",
                                ticket,
                                paymentIntent,
                            },
                            null,
                            2
                        ),
                    },
                ],
            };
        }

        case "get_my_tickets": {
            let filteredTickets = Array.from(tickets.values());

            if (args?.status) {
                filteredTickets = filteredTickets.filter(
                    (t) => t.status === args.status
                );
            }

            return {
                content: [
                    {
                        type: "text" as const,
                        text: JSON.stringify(
                            {
                                success: true,
                                count: filteredTickets.length,
                                tickets: filteredTickets,
                            },
                            null,
                            2
                        ),
                    },
                ],
            };
        }

        default:
            throw new Error(`Unknown tool: ${name}`);
    }
});

/**
 * Resource listings
 */
server.setRequestHandler(ListResourcesRequestSchema, async () => {
    return {
        resources: [
            {
                uri: "ticket://events",
                name: "All Events",
                description: "Complete list of all available events",
                mimeType: "application/json",
            },
            {
                uri: "ticket://venues",
                name: "All Venues",
                description: "Complete list of all venues",
                mimeType: "application/json",
            },
        ],
    };
});

/**
 * Resource reading
 */
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const { uri } = request.params;

    switch (uri) {
        case "ticket://events":
            return {
                contents: [
                    {
                        uri,
                        mimeType: "application/json",
                        text: JSON.stringify(
                            Array.from(events.values()),
                            null,
                            2
                        ),
                    },
                ],
            };

        case "ticket://venues":
            return {
                contents: [
                    {
                        uri,
                        mimeType: "application/json",
                        text: JSON.stringify(
                            Array.from(venues.values()),
                            null,
                            2
                        ),
                    },
                ],
            };

        default:
            throw new Error(`Unknown resource: ${uri}`);
    }
});

// Start the MCP server
async function runServer() {
    const transport = new StdioServerTransport();
    await server.connect(transport);

    const PORT = process.env.PORT || 3000;

    console.log(`🎫 MCP Ticket Sales Server starting...`);
    console.log(`📍 Port: ${PORT}`);
    console.log(`💳 HTTP 402 Payment Support: Enabled`);
    console.log(`🪙 Coinbase Commerce Integration: Ready`);
    console.log(`✅ MCP Server Ready!`);
}

// Export server for use
export { server };

// Start server if run directly
runServer().catch(console.error);
