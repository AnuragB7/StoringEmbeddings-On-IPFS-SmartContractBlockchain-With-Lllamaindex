import os
import json
import asyncio
from web3 import Web3
from dotenv import load_dotenv
from manual_system import UserManualSystem  # We'll create this next

# Load contract ABI
def load_contract_abi():
    
    # Path to your contract JSON file from truffle build
    contract_path = "./manual-contract/build/contracts/ManualRegistry.json"
    with open(contract_path) as f:
        contract_json = json.load(f)
        return contract_json['abi']

async def test_system():
    # Load environment variables
    load_dotenv()
    
    # Check if environment variables are loaded
    contract_address = os.getenv('CONTRACT_ADDRESS')
    account_address = os.getenv('ACCOUNT_ADDRESS')
    
    if not contract_address or not account_address:
        raise ValueError("Environment variables not loaded. Check your .env file.")
    
    print(f"Contract Address: {contract_address}")
    print(f"Account Address: {account_address}")
    
     # Get addresses and convert to checksum format
    contract_address = Web3.to_checksum_address(os.getenv('CONTRACT_ADDRESS'))
    account_address = Web3.to_checksum_address(os.getenv('ACCOUNT_ADDRESS'))
    

    system = UserManualSystem(
        contract_address=contract_address,
        contract_abi=load_contract_abi(),
        web3_provider=os.getenv('WEB3_PROVIDER'),
        ipfs_url="/ip4/127.0.0.1/tcp/5001",
        openai_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Test manual content
    manual_content = """
    Equipment Safety Protocol
    
    1. Pre-operation Checks
    Before operating the machine, ensure power is disconnected.
    Check all safety guards are in place.
    Verify emergency stop button is accessible.
    
    2. Startup Procedure
    Connect power supply to designated outlet.
    Press the green start button.
    Wait for system initialization (30 seconds).
    """
    
    try:
        # Upload manual
        print("Uploading manual...")
        content_cid, embeddings_cid = await system.upload_manual(
            manual_id="TEST_001",
            content=manual_content,
            account_address=os.getenv('ACCOUNT_ADDRESS'),
            private_key=os.getenv('PRIVATE_KEY')
        )
        print(f"Manual uploaded successfully!")
        print(f"Content CID: {content_cid}")
        print(f"Embeddings CID: {embeddings_cid}")
        
        # Test query
        print("\nTesting query...")
        query = "What should I check before starting the machine?"
        results = await system.query_manual(
            manual_id="TEST_001",
            query=query,
            account_address=os.getenv('ACCOUNT_ADDRESS')
        )
        
        print("\nQuery results:")
        for result in results:
            print(f"Chunk: {result['chunk']}")
            print(f"Score: {result['score']}")
            print("---")
        
        # Generate response
        print("\nGenerating response...")
        response = await system.generate_response(query, results)
        print(f"AI Response: {response}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_system())