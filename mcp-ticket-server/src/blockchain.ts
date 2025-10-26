/**
 * Blockchain Service for Base Sepolia
 * Handles USDC ticket purchases via on-chain transactions
 */

import { ethers } from "ethers";

// Base Sepolia configuration
const BASE_SEPOLIA_RPC =
    process.env.BASE_SEPOLIA_RPC || "https://sepolia.base.org";
const BASE_SEPOLIA_CHAIN_ID = 84532;

// USDC Contract on Base Sepolia
const USDC_CONTRACT_ADDRESS =
    process.env.USDC_CONTRACT_ADDRESS ||
    "0x036CbD53842c5426634e7929541eC2318f3dCF7e";

// ERC-20 ABI (minimal - just what we need for USDC)
const ERC20_ABI = [
    "function balanceOf(address owner) view returns (uint256)",
    "function transfer(address to, uint256 amount) returns (bool)",
    "function approve(address spender, uint256 amount) returns (bool)",
    "function allowance(address owner, address spender) view returns (uint256)",
    "function decimals() view returns (uint8)",
    "function symbol() view returns (string)",
    "event Transfer(address indexed from, address indexed to, uint256 value)",
];

// Payment wallet (will receive and send ticket payments)
let paymentWallet: ethers.HDNodeWallet | ethers.Wallet;
let provider: ethers.JsonRpcProvider;
let usdcContract: ethers.Contract;

export interface BlockchainPayment {
    ticketId: string;
    paymentAddress: string;
    amountUSDC: string;
    amountUSD: number;
    expiresAt: string;
    transactionHash?: string;
    status: "pending" | "confirmed" | "failed" | "expired";
}

/**
 * Initialize blockchain service with USDC support
 */
export function initializeBlockchain(privateKey?: string) {
    try {
        provider = new ethers.JsonRpcProvider(BASE_SEPOLIA_RPC);

        if (privateKey) {
            // Remove 0x prefix if present
            const cleanKey = privateKey.startsWith("0x")
                ? privateKey.slice(2)
                : privateKey;
            paymentWallet = new ethers.Wallet(cleanKey, provider);
            console.log("💎 Blockchain Service Initialized");
            console.log(`📬 Agent Wallet Address: ${paymentWallet.address}`);
            console.log(`💵 USDC Contract: ${USDC_CONTRACT_ADDRESS}`);
        } else {
            // Generate a temporary wallet for testing
            paymentWallet = ethers.Wallet.createRandom(provider);
            console.log(
                "⚠️  Using temporary wallet (set PAYMENT_WALLET_PRIVATE_KEY in .env)"
            );
            console.log(`📬 Agent Wallet Address: ${paymentWallet.address}`);
            console.log(`🔑 Private Key: ${paymentWallet.privateKey}`);
            console.log(`💡 Add this to your .env file to persist the wallet`);
        }

        // Initialize USDC contract
        usdcContract = new ethers.Contract(
            USDC_CONTRACT_ADDRESS,
            ERC20_ABI,
            paymentWallet
        );

        return {
            address: paymentWallet.address,
            chainId: BASE_SEPOLIA_CHAIN_ID,
            network: "Base Sepolia",
            usdcAddress: USDC_CONTRACT_ADDRESS,
        };
    } catch (error) {
        console.error("Failed to initialize blockchain:", error);
        throw error;
    }
}

/**
 * Convert USD amount to USDC (6 decimals)
 * USDC uses 6 decimals, so $100 = 100000000 (100 * 10^6)
 */
function convertUSDtoUSDC(amountUSD: number): string {
    // USDC has 6 decimals
    const usdcAmount = Math.floor(amountUSD * 1_000_000);
    return usdcAmount.toString();
}

/**
 * Create a USDC payment request for ticket purchase
 */
export async function createPaymentRequest(
    ticketId: string,
    amountUSD: number,
    expirationMinutes: number = 30
): Promise<BlockchainPayment> {
    const amountUSDC = convertUSDtoUSDC(amountUSD);

    const payment: BlockchainPayment = {
        ticketId,
        paymentAddress: paymentWallet.address,
        amountUSDC,
        amountUSD,
        expiresAt: new Date(
            Date.now() + expirationMinutes * 60 * 1000
        ).toISOString(),
        status: "pending",
    };

    return payment;
}

/**
 * Check if USDC payment has been received
 */
export async function checkPayment(
    paymentAddress: string,
    expectedAmountUSDC: string
): Promise<{
    received: boolean;
    transactionHash?: string;
    actualAmount?: string;
}> {
    try {
        // Check USDC balance
        const balance = await usdcContract.balanceOf(paymentAddress);

        // Convert expected amount to BigInt for comparison
        const expectedAmount = BigInt(expectedAmountUSDC);

        if (balance >= expectedAmount) {
            // Format for display (USDC has 6 decimals)
            const displayBalance = (Number(balance) / 1_000_000).toFixed(2);
            return {
                received: true,
                actualAmount: displayBalance,
            };
        }

        return { received: false };
    } catch (error) {
        console.error("Error checking USDC payment:", error);
        return { received: false };
    }
}

/**
 * Monitor for incoming transaction
 */
export async function monitorPayment(
    paymentAddress: string,
    expectedAmountUSDC: string,
    timeoutMinutes: number = 30
): Promise<BlockchainPayment | null> {
    return new Promise((resolve) => {
        const timeout = setTimeout(() => {
            provider.off("block");
            resolve(null);
        }, timeoutMinutes * 60 * 1000);

        provider.on("block", async (_blockNumber: number) => {
            const result = await checkPayment(
                paymentAddress,
                expectedAmountUSDC
            );

            if (result.received) {
                clearTimeout(timeout);
                provider.off("block");

                resolve({
                    ticketId: "",
                    paymentAddress,
                    amountUSDC: expectedAmountUSDC,
                    amountUSD: 0,
                    expiresAt: new Date().toISOString(),
                    transactionHash: result.transactionHash,
                    status: "confirmed",
                });
            }
        });
    });
}

/**
 * Verify a transaction hash
 */
export async function verifyTransaction(txHash: string): Promise<{
    valid: boolean;
    amount?: string;
    from?: string;
    to?: string;
    confirmations?: number;
}> {
    try {
        const tx = await provider.getTransaction(txHash);

        if (!tx) {
            return { valid: false };
        }

        const receipt = await provider.getTransactionReceipt(txHash);

        // Handle confirmations which can be a number or a function returning Promise<number>
        let confirmations = 0;
        if (receipt?.confirmations) {
            const conf = receipt.confirmations;
            confirmations = typeof conf === 'number' ? conf : await (conf as () => Promise<number>)();
        }

        return {
            valid: true,
            amount: ethers.formatEther(tx.value),
            from: tx.from,
            to: tx.to || undefined,
            confirmations,
        };
    } catch (error) {
        console.error("Error verifying transaction:", error);
        return { valid: false };
    }
}

/**
 * Get network info
 */
export async function getNetworkInfo() {
    try {
        const network = await provider.getNetwork();
        const blockNumber = await provider.getBlockNumber();
        const gasPrice = await provider.getFeeData();

        return {
            chainId: Number(network.chainId),
            blockNumber,
            gasPrice: ethers.formatUnits(gasPrice.gasPrice || 0, "gwei"),
        };
    } catch (error) {
        console.error("Error getting network info:", error);
        return null;
    }
}

/**
 * Send USDC payment to an address
 */
export async function sendPayment(
    toAddress: string,
    amountUSD: string,
    fromWallet?: ethers.Wallet
): Promise<{
    success: boolean;
    transactionHash?: string;
    error?: string;
}> {
    try {
        const wallet = fromWallet || paymentWallet;

        if (!wallet) {
            return { success: false, error: "No wallet configured" };
        }

        // Convert USD to USDC amount (6 decimals)
        const amountUSDC = convertUSDtoUSDC(parseFloat(amountUSD));

        // Check USDC balance
        const balance = await usdcContract.balanceOf(wallet.address);
        const balanceUSD = (Number(balance) / 1_000_000).toFixed(2);

        if (balance < BigInt(amountUSDC)) {
            return {
                success: false,
                error: `Insufficient USDC balance. Have $${balanceUSD} USDC, need $${amountUSD} USDC`,
            };
        }

        // Send USDC transfer transaction
        const tx = await usdcContract.transfer(toAddress, amountUSDC);

        console.log(`💸 Sending $${amountUSD} USDC to ${toAddress}`);
        console.log(`🔗 Transaction hash: ${tx.hash}`);

        // Wait for confirmation
        const receipt = await tx.wait();

        console.log(
            `✅ Transaction confirmed in block ${receipt?.blockNumber}`
        );

        return {
            success: true,
            transactionHash: tx.hash,
        };
    } catch (error: any) {
        console.error("Error sending USDC payment:", error);
        return {
            success: false,
            error: error.message || "Unknown error",
        };
    }
}

/**
 * Get wallet USDC balance
 */
export async function getWalletBalance(address?: string): Promise<{
    balance: string;
    balanceRaw: bigint;
    balanceETH?: string;
}> {
    const addr = address || paymentWallet.address;

    // Get USDC balance
    const usdcBalance = await usdcContract.balanceOf(addr);
    const balanceUSD = (Number(usdcBalance) / 1_000_000).toFixed(2);

    // Also get ETH balance for gas
    const ethBalance = await provider.getBalance(addr);
    const balanceETH = ethers.formatEther(ethBalance);

    return {
        balance: balanceUSD,
        balanceRaw: usdcBalance,
        balanceETH,
    };
}

/**
 * Estimate gas for a USDC transaction
 */
export async function estimateGas(
    toAddress: string,
    amountUSD: string
): Promise<{
    gasEstimate: string;
    gasPrice: string;
    totalCostETH: string;
}> {
    try {
        const amountUSDC = convertUSDtoUSDC(parseFloat(amountUSD));
        const feeData = await provider.getFeeData();

        // Estimate gas for ERC-20 transfer (typically ~65000 gas)
        const gasEstimate = await usdcContract.transfer.estimateGas(
            toAddress,
            amountUSDC
        );
        const gasPrice = feeData.gasPrice || 0n;

        const gasCost = gasEstimate * gasPrice;

        return {
            gasEstimate: gasEstimate.toString(),
            gasPrice: ethers.formatUnits(gasPrice, "gwei"),
            totalCostETH: ethers.formatEther(gasCost),
        };
    } catch (error) {
        console.error("Error estimating gas:", error);
        return {
            gasEstimate: "65000",
            gasPrice: "0",
            totalCostETH: "0",
        };
    }
}

export { provider, paymentWallet };
