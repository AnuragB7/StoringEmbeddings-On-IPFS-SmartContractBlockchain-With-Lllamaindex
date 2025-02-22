# StoringEmbeddings-On-IPFS-SmartContractBlockchain-With-Lllamaindex

## Create a new directory for the Python implementation:

mkdir manual-system
cd manual-system

1. Install Required Dependencies

pip install web3 ipfsapi openai numpy python-dotenv


2. Setup IPFS

IPFS is a peer-to-peer protocol and network for storing and sharing data in a distributed system. Let me break down its key aspects and benefits:
Core Concept: IPFS creates a decentralized system for storing and accessing files, websites, applications, and data. Instead of using location-based addressing (like HTTP's URLs), it uses content-based addressing - files are identified by their content, not where they're stored.
Key Benefits:
1. Decentralization and Reliability
* No single point of failure since files are distributed across many nodes
* Content remains accessible even if some nodes go offline
* Better resilience against censorship and network outages
2. Efficient Data Transfer
* Downloads data from multiple sources simultaneously
* Reduces bandwidth costs and server load
* Only transfers unique pieces of data, avoiding duplicate content
3. Content Integrity
* Files are cryptographically hashed, ensuring content hasn't been tampered with
* Content addressing means you always get exactly what you requested
* Built-in version control for content changes
4. Offline-First Capabilities
* Content can be accessed without constant internet connection
* Users can share files directly between devices on local networks
* Improved performance in areas with limited connectivity
5. Storage Efficiency
* Deduplicates identical files automatically
* Only stores one copy of identical content across the network
* Reduces overall storage requirements
Practical Applications:
* Hosting websites that are resistant to censorship
* Sharing large datasets efficiently
* Building decentralized applications (dApps)
* Creating permanent, immutable archives
* Improving content delivery networks

- First, install IPFS CLI from: https://docs.ipfs.tech/install/command-line/
- Initialize and start IPFS daemon:

If you are on Mac use brew : brew install ipfs

### bash
#Initialize IPFS

ipfs init



## Start the IPFS daemon

Generally when we start IPFS daemon it by default takes port 8080 , if this port is busy you can change the port 

You'll need to modify the IPFS config file. Here's how:

Stop the IPFS daemon if it's running (Ctrl+C)
Configure IPFS to use port 8007:

### bash

ipfs config Addresses.Gateway "/ip4/127.0.0.1/tcp/8007"

Verify the change:

### bash

ipfs config show | grep Gateway

Start the daemon :

### bash

ipfs daemon


This will start your local IPFS node at /ip4/127.0.0.1/tcp/5001


## Setup Smart Contract

First, install Truffle for contract deployment:

Truffle is a popular development framework for Ethereum that makes it easier to build and test blockchain applications (dApps). 

Key features:

Development Environment: Provides a complete suite for writing, testing, and deploying smart contracts
Built-in Smart Contract Compilation: Automatically compiles Solidity contracts
Automated Testing: Includes a testing framework for both JavaScript and Solidity tests
Deployment Management: Handles deploying contracts to different networks
Network Management: Supports multiple networks and network configurations
Interactive Console: Provides a REPL (console) for direct blockchain interaction
Contract Migration: Manages contract deployment scripts ("migrations")
Asset Pipeline: Manages frontend assets like JavaScript, CSS, and images

Truffle is part of the broader Truffle Suite, which includes:

Ganache: A personal blockchain for development and testing
Drizzle: A collection of frontend libraries for dApp development

The framework uses JavaScript and works with the Ethereum Virtual Machine (EVM). It's particularly useful for developers who want to write smart contracts in Solidity and build decentralized applications on Ethereum.


### bash

npm install -g truffle


For local development, you'll need to set up a local blockchain network first. The most common way is to use Ganache. Here's how to set it up:

First, install Ganache:

### bash

npm install -g ganache

## Start Ganache:

Ganache is a personal blockchain environment that runs on your computer. It's part of the Truffle Suite and is designed specifically for development and testing purposes. Here's a comprehensive explanation:
Key Features:

Personal Blockchain


Creates a local Ethereum blockchain on your computer
Provides 10 default accounts pre-funded with test Ether
Mimics the behavior of a real Ethereum network but in a controlled environment


Development Tools


Visual interface to view accounts, blocks, transactions, and contract events
Ability to mine blocks instantly or on a set time interval
Gas price and limit customization
Network ID customization
Advanced mining controls


Testing Capabilities


Deterministic account generation (same accounts every time using a seed phrase)
Customizable block time
Error handling and debugging tools
State manipulation features

Two Versions:

Ganache UI (formerly Ganache Desktop)


Graphical user interface
Visual blockchain explorer
Easy-to-use workspace management
Real-time transaction monitoring


Ganache CLI (formerly TestRPC)


Command-line interface
More suitable for automated testing and CI/CD pipelines
Greater flexibility for configuration
Easier to script and automate

Common Use Cases:

Testing smart contracts
Developing dApps without spending real Ether
Debugging transactions
Teaching and learning blockchain development
Running automated tests
Simulating different network conditions

### bash
ganache



## Create a new directory for your smart contract:

### bash

mkdir manual-contract
cd manual-contract
truffle init

This will create a basic project structure:

Copymanual-contract/
├── contracts/
├── migrations/
├── test/
└── truffle-config.js

### bash

touch contracts/ManualRegistry.sol

Copy below content into ManualRegistry.sol :

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ManualRegistry {
    struct Manual {
        string contentCID;
        string embeddingsCID;
        uint256 version;
        address owner;
        bool isActive;
        mapping(address => bool) authorizedUsers;
    }
    
    mapping(string => Manual) public manuals;
    
    event ManualUploaded(string manualId, string contentCID, string embeddingsCID);
    event AccessGranted(string manualId, address user);
    
    function uploadManual(
        string memory manualId,
        string memory contentCID,
        string memory embeddingsCID,
        uint256 version
    ) public {
        Manual storage manual = manuals[manualId];
        manual.contentCID = contentCID;
        manual.embeddingsCID = embeddingsCID;
        manual.version = version;
        manual.owner = msg.sender;
        manual.isActive = true;
        manual.authorizedUsers[msg.sender] = true;
        
        emit ManualUploaded(manualId, contentCID, embeddingsCID);
    }
    
    function grantAccess(string memory manualId, address user) public {
        require(manuals[manualId].owner == msg.sender, "Not authorized");
        manuals[manualId].authorizedUsers[user] = true;
        emit AccessGranted(manualId, user);
    }
    
    function getManualCIDs(string memory manualId) public view returns (string memory, string memory) {
        require(manuals[manualId].authorizedUsers[msg.sender], "Not authorized");
        return (manuals[manualId].contentCID, manuals[manualId].embeddingsCID);
    }
}


## Create a migration file in migrations/2_deploy_manual_registry.js:

### bash

touch migrations/2_deploy_manual_registry.js

Add this content to 2_deploy_manual_registry.js:

const ManualRegistry = artifacts.require("ManualRegistry");

module.exports = function(deployer) {
  deployer.deploy(ManualRegistry);
};


## Update truffle-config.js:

module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",
      port: 8545,
      network_id: "*"
    }
  },
  compilers: {
    solc: {
      version: "0.8.0"
    }
  }
};


## Start Ganache in a separate terminal:

### bash
ganache

## Now deploying :

### bash
truffle compile
truffle migrate --network development

## Create a .env file:

### bash
cd manual-system
touch .env

Add your configuration to .env:

WEB3_PROVIDER=http://127.0.0.1:8545
CONTRACT_ADDRESS=YOUR_CONTRACT_ADDRESS  # The address you got from truffle deploy
OPENAI_API_KEY=YOUR_OPENAI_KEY
ACCOUNT_ADDRESS=YOUR_GANACHE_ACCOUNT  # First account address from Ganache
PRIVATE_KEY=YOUR_GANACHE_PRIVATE_KEY  # First account private key from Ganache


