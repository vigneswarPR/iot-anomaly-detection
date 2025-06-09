// smart_contract/hardhat.config.js

require("@nomicfoundation/hardhat-toolbox"); // This imports essential Hardhat plugins, including ethers.js

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  // Specify the Solidity compiler version for your contracts.
  // Make sure this matches the `pragma solidity` declaration in your AnomalyLogger.sol
  solidity: "0.8.0", // Or "0.8.24" if that's what you decided for your contract.

  // Define the networks Hardhat can interact with.
  networks: {
    // This configures a network named 'ganache'
    ganache: {
      url: "http://127.0.0.1:8545", // The default RPC URL where Ganache typically runs.
                                   // Ensure your Ganache application/CLI is running on this address.

      // For local development with Ganache, you usually don't need to specify
      // accounts here, as Hardhat's ethers plugin will use the default accounts
      // provided by Ganache when you send transactions.
      // If you were deploying to a public testnet or mainnet, you would
      // definitely need to specify your private key here (or via environment variables).
      // Example (for reference only, do not hardcode private keys in production):
      // accounts: ["0x...YOUR_GANACHE_ACCOUNT_PRIVATE_KEY_HERE..."]
    },
    // You can add other networks here later, e.g., sepolia, mainnet, etc.
    // sepolia: {
    //   url: "YOUR_SEPOLIA_RPC_URL",
    //   accounts: ["YOUR_PRIVATE_KEY_FOR_SEPOLIA_TESTNET_ACCOUNT"]
    // }
  },

  // Optional: Configure paths for your project if they differ from the default Hardhat structure.
  // This usually isn't necessary for basic projects.
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  },

  // Optional: Configure Solidity compiler settings (e.g., optimizer, evmVersion).
  // Usually fine with defaults for a hackathon.
  // compilers: {
  //   solc: {
  //     version: "0.8.28", // Must match the solidity version above
  //     settings: {
  //       optimizer: {
  //         enabled: true,
  //         runs: 200
  //       },
  //       evmVersion: "shanghai" // Match your chain's EVM version
  //     }
  //   }
  // }
};