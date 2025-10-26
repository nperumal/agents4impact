/**
 * Express-based MCP Ticket Sales Server with Blockchain Payment Support
 * Base Sepolia Network Integration
 */

import express from "express";
import cors from "cors";
import { v4 as uuidv4 } from "uuid";
import { config } from "dotenv";
import { ethers } from "ethers";
import { events, venues, tickets, paymentIntents } from "./data.js";
import { Ticket, PaymentIntent, PaymentResponse } from "./types.js";
import {
    initializeBlockchain,
    createPaymentRequest,
    verifyTransaction,
    getNetworkInfo,
    checkPayment,
    sendPayment,
    getWalletBalance,
    estimateGas,
} from "./blockchain.js";

// Load environment variables
config();

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3000;

// Initialize blockchain on startup
let blockchainInfo: any;
try {
    blockchainInfo = initializeBlockchain(
        process.env.PAYMENT_WALLET_PRIVATE_KEY
    );
} catch (error) {
    console.error("⚠️  Blockchain initialization failed:", error);
}

// Health check
app.get("/health", async (_req, res) => {
    const networkInfo = await getNetworkInfo();
    res.json({
        status: "healthy",
        server: "MCP Ticket Sales Server",
        blockchain: blockchainInfo,
        network: networkInfo,
    });
});

// List events
app.post("/mcp/tool/list_events", (req, res) => {
    const { category, city } = req.body;
    let filteredEvents = Array.from(events.values());

    if (category) {
        filteredEvents = filteredEvents.filter((e) => e.category === category);
    }

    if (city) {
        filteredEvents = filteredEvents.filter((e) => {
            const venue = venues.get(e.venueId);
            return venue?.city.toLowerCase().includes(city.toLowerCase());
        });
    }

    res.json({
        success: true,
        count: filteredEvents.length,
        events: filteredEvents,
    });
});

// Get event details
app.post("/mcp/tool/get_event", (req, res) => {
    const { eventId } = req.body;
    const event = events.get(eventId);

    if (!event) {
        return res.json({ success: false, error: "Event not found" });
    }

    const venue = venues.get(event.venueId);

    return res.json({
        success: true,
        event,
        venue,
    });
});

// List venues
app.post("/mcp/tool/list_venues", (req, res) => {
    const { city } = req.body;
    let filteredVenues = Array.from(venues.values());

    if (city) {
        filteredVenues = filteredVenues.filter((v) =>
            v.city.toLowerCase().includes(city.toLowerCase())
        );
    }

    res.json({
        success: true,
        count: filteredVenues.length,
        venues: filteredVenues,
    });
});

// Purchase tickets (Blockchain payment flow)
app.post("/mcp/tool/purchase_tickets", async (req, res) => {
    const { eventId, quantity } = req.body;
    const event = events.get(eventId);

    if (!event) {
        return res.json({
            success: false,
            requiresPayment: false,
            error: "Event not found",
        });
    }

    if (event.availableTickets < quantity) {
        return res.json({
            success: false,
            requiresPayment: false,
            error: `Only ${event.availableTickets} tickets available`,
        });
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

    // Create blockchain payment request
    const blockchainPayment = await createPaymentRequest(
        ticketId,
        totalAmount,
        30
    );

    // Create payment intent with blockchain details
    const paymentIntentId = uuidv4();
    const paymentIntent: PaymentIntent = {
        id: paymentIntentId,
        ticketId: ticketId,
        amount: totalAmount,
        currency: "USD",
        status: "pending",
        createdAt: new Date().toISOString(),
        expiresAt: blockchainPayment.expiresAt,
    };

    // Add blockchain payment details
    (paymentIntent as any).blockchain = {
        network: "Base Sepolia",
        chainId: 84532,
        paymentAddress: blockchainPayment.paymentAddress,
        amountUSDC: blockchainPayment.amountUSDC,
        amountUSD: blockchainPayment.amountUSD,
        currency: "USDC",
    };

    paymentIntents.set(paymentIntentId, paymentIntent);

    // Return HTTP 402 Payment Required response with blockchain details
    const response: PaymentResponse = {
        success: false,
        requiresPayment: true,
        ticket: ticket,
        paymentIntent: paymentIntent,
    };

    return res.json(response);
});

// Check payment status (with blockchain verification)
app.post("/mcp/tool/check_payment_status", async (req, res) => {
    const { paymentIntentId } = req.body;
    const paymentIntent = paymentIntents.get(paymentIntentId);

    if (!paymentIntent) {
        return res.json({ success: false, error: "Payment intent not found" });
    }

    const ticket = tickets.get(paymentIntent.ticketId);

    // Check blockchain for payment if still pending
    if (
        paymentIntent.status === "pending" &&
        (paymentIntent as any).blockchain
    ) {
        const blockchain = (paymentIntent as any).blockchain;
        const paymentCheck = await checkPayment(
            blockchain.paymentAddress,
            blockchain.amountUSDC
        );

        if (paymentCheck.received) {
            // Payment confirmed! Update status
            paymentIntent.status = "completed";
            (paymentIntent as any).blockchain.transactionHash =
                paymentCheck.transactionHash;

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
        }
    }

    return res.json({
        success: true,
        paymentIntent,
        ticket,
    });
});

// Verify blockchain transaction
app.post("/mcp/tool/verify_transaction", async (req, res) => {
    const { paymentIntentId, transactionHash } = req.body;

    if (!transactionHash) {
        return res.json({ success: false, error: "Transaction hash required" });
    }

    const paymentIntent = paymentIntentId
        ? paymentIntents.get(paymentIntentId)
        : null;

    // Verify the transaction on blockchain
    const txVerification = await verifyTransaction(transactionHash);

    if (!txVerification.valid) {
        return res.json({ success: false, error: "Invalid transaction" });
    }

    // If payment intent provided, update it
    if (paymentIntent && (paymentIntent as any).blockchain) {
        const blockchain = (paymentIntent as any).blockchain;

        // Check if transaction is to the correct address and has correct amount
        if (
            txVerification.to?.toLowerCase() ===
            blockchain.paymentAddress.toLowerCase()
        ) {
            const paidAmount = parseFloat(txVerification.amount || "0");
            const expectedAmount = parseFloat(blockchain.amountETH);

            if (paidAmount >= expectedAmount * 0.99) {
                // Allow 1% slippage
                paymentIntent.status = "completed";
                blockchain.transactionHash = transactionHash;
                blockchain.confirmations = txVerification.confirmations;

                // Update ticket
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

                return res.json({
                    success: true,
                    message: "Payment confirmed on blockchain",
                    transaction: txVerification,
                    paymentIntent,
                    ticket,
                });
            }
        }
    }

    return res.json({
        success: true,
        message: "Transaction verified",
        transaction: txVerification,
    });
});

// Get my tickets
app.post("/mcp/tool/get_my_tickets", (req, res) => {
    const { status } = req.body;
    let filteredTickets = Array.from(tickets.values());

    if (status) {
        filteredTickets = filteredTickets.filter((t) => t.status === status);
    }

    res.json({
        success: true,
        count: filteredTickets.length,
        tickets: filteredTickets,
    });
});

// Get most recent pending payment
app.post("/mcp/tool/get_pending_payment", (_req, res) => {
    // Find the most recent pending payment intent
    let mostRecentPending: any = null;
    let mostRecentTime = 0;

    paymentIntents.forEach((paymentIntent, id) => {
        if (paymentIntent.status === "pending") {
            const createdAt = new Date(paymentIntent.createdAt).getTime();
            if (createdAt > mostRecentTime) {
                mostRecentTime = createdAt;
                mostRecentPending = {
                    ...paymentIntent,
                    id,
                };
            }
        }
    });

    if (!mostRecentPending) {
        return res.json({
            success: false,
            error: "No pending payments found. Please purchase a ticket first.",
        });
    }

    // Return payment details
    return res.json({
        success: true,
        paymentIntent: mostRecentPending,
    });
});

// Send payment (for agent-initiated transactions)
app.post("/mcp/tool/send_payment", async (req, res) => {
    const { toAddress, amountUSD, memo } = req.body;

    if (!toAddress || !amountUSD) {
        return res.json({
            success: false,
            error: "toAddress and amountUSD are required",
        });
    }

    // Validate address
    if (!ethers.isAddress(toAddress)) {
        return res.json({
            success: false,
            error: "Invalid Ethereum address",
        });
    }

    // Check balance first
    const balanceInfo = await getWalletBalance();
    const estimatedCost = await estimateGas(toAddress, amountUSD);

    console.log(`📤 Payment request: $${amountUSD} USDC to ${toAddress}`);
    console.log(`💰 Current USDC balance: $${balanceInfo.balance}`);
    console.log(
        `💰 Current ETH balance (for gas): ${balanceInfo.balanceETH} ETH`
    );
    console.log(`⛽ Estimated gas cost: ${estimatedCost.totalCostETH} ETH`);

    // Send the payment
    const result = await sendPayment(toAddress, amountUSD);

    if (result.success) {
        return res.json({
            success: true,
            transactionHash: result.transactionHash,
            amountUSD,
            currency: "USDC",
            toAddress,
            memo,
            explorerUrl: `https://sepolia.basescan.org/tx/${result.transactionHash}`,
        });
    } else {
        return res.json({
            success: false,
            error: result.error,
        });
    }
});

// Get wallet balance
app.get("/mcp/tool/get_balance", async (_req, res) => {
    const balanceInfo = await getWalletBalance();
    res.json({
        success: true,
        address: blockchainInfo?.address,
        balanceUSDC: balanceInfo.balance,
        balanceETH: balanceInfo.balanceETH,
        network: "Base Sepolia",
        chainId: 84532,
        usdcContract: blockchainInfo?.usdcAddress,
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`\n🎫 MCP Ticket Sales Server`);
    console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    console.log(`📍 Port: ${PORT}`);
    console.log(`⛓️  Blockchain: Base Sepolia (Chain ID: 84532)`);
    console.log(`💵 Payment Method: USDC (Stablecoin)`);
    console.log(
        `📬 Payment Address: ${blockchainInfo?.address || "Not configured"}`
    );
    console.log(`✅ Server Ready!`);
    console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);
});

export default app;
