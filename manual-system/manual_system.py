import os
import json
import openai
import ipfsapi
import requests
import asyncio
import numpy as np
from web3 import Web3
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass
from llama_index.core import Settings 
from typing import List, Dict, Tuple, Optional
from llama_index.embeddings.openai import OpenAIEmbedding

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
api_base = os.getenv('OPENAI_API_BASE')
embed_model= OpenAIEmbedding(
                    model_name="text-embedding-bge-m3",
                    api_key=api_key,
                    api_base=api_base,
                )
Settings.embed_model=embed_model

@dataclass
class ManualChunk:
    text: str
    start_index: int
    embedding: np.ndarray

@dataclass
class ManualChunk:
    text: str
    start_index: int
    embedding: np.ndarray

class UserManualSystem:
    def __init__(
        self,
        contract_address: str,
        contract_abi: str,
        web3_provider: str,
        ipfs_url: str,
        openai_key: str
    ):
        """Initialize the user manual system."""
        # Setup Web3
        self.w3 = Web3(Web3.HTTPProvider(web3_provider))
        checksum_address = Web3.to_checksum_address(contract_address)
        self.contract = self.w3.eth.contract(
            address=checksum_address,
            abi=contract_abi
        )
        
        # Setup IPFS endpoint
        self.ipfs_endpoint = 'http://127.0.0.1:5001/api/v0'
        
        # Setup OpenAI
        openai.api_key = openai_key

    def _ipfs_add_json(self, json_data):
        """Add JSON data to IPFS."""
        files = {
            'file': ('data.json', json.dumps(json_data))
        }
        response = requests.post(f'{self.ipfs_endpoint}/add', files=files)
        return response.json()['Hash']

    def _ipfs_get_json(self, cid):
        """Get JSON data from IPFS."""
        response = requests.post(f'{self.ipfs_endpoint}/cat?arg={cid}')
        return json.loads(response.content)

    async def upload_manual(
    self,
    manual_id: str,
    content: str,
    account_address: str,
    private_key: str
    ) -> Tuple[str, str]:
        try:
            # Split manual into chunks
            chunks_with_positions = self._split_manual(content)
            chunks = [chunk[0] for chunk in chunks_with_positions]
            
            # Create embeddings
            embeddings = await self.create_embeddings(chunks)
            
            # Prepare manual data structure
            manual_data = {
                'content': content,
                'chunks': [
                    {
                        'text': chunk[0],
                        'position': chunk[1],
                        'embedding': emb.tolist()
                    }
                    for chunk, emb in zip(chunks_with_positions, embeddings)
                ]
            }
            
            # Store content in IPFS
            content_cid = self._ipfs_add_json(manual_data)
            
            # Store embeddings separately
            embeddings_data = {
                'embeddings': [emb.tolist() for emb in embeddings],
                'chunk_positions': [chunk[1] for chunk in chunks_with_positions]
            }
            embeddings_cid = self._ipfs_add_json(embeddings_data)
            
            # Register in smart contract
            checksum_address = Web3.to_checksum_address(account_address)
            nonce = self.w3.eth.get_transaction_count(checksum_address)
            
            transaction = self.contract.functions.uploadManual(
                manual_id,
                content_cid,
                embeddings_cid,
                1  # version
            ).build_transaction({
                'chainId': 1337,  # Ganache chain ID
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
                'from': checksum_address
            })
            
            # Sign the transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                private_key
            )
            
            # Send the raw transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)  # Changed from rawTransaction to raw_transaction
            
            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return content_cid, embeddings_cid
            
        except Exception as e:
            raise Exception(f"Failed to upload manual: {str(e)}")
        
    def _split_manual(self, text: str, chunk_size: int = 1000) -> List[Tuple[str, int]]:
        """Split manual into chunks with positions."""
        chunks = []
        current_pos = 0
        
        # Split into sentences and create chunks
        sentences = [s.strip() + '.' for s in text.split('.') if s.strip()]
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            if current_length + len(sentence) > chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append((chunk_text, current_pos))
                current_pos += len(chunk_text) + 1
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence)
        
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append((chunk_text, current_pos))
            
        return chunks

    async def create_embeddings(self, text_chunks: List[str]) -> List[np.ndarray]:
        """Create embeddings for text chunks using LlamaIndex OpenAIEmbedding."""
        embeddings = []
        for chunk in text_chunks:
            # LlamaIndex embedding returns List[float], convert to numpy array
            embedding_response = embed_model.get_text_embedding(chunk)
            embedding = np.array(embedding_response, dtype=np.float32)
            embeddings.append(embedding)
        return embeddings


    async def query_manual(
    self,
    manual_id: str,
    query: str,
    account_address: str,
    top_k: int = 3
    ) -> List[Dict]:
        """Query manual content using semantic search."""
        try:
            # Get CIDs from contract - remove await and use call() directly
            content_cid, embeddings_cid = self.contract.functions.getManualCIDs(
                manual_id
            ).call({'from': account_address})
            
            # Get query embedding - create_embeddings already returns a list
            query_embeddings = await self.create_embeddings([query])
            query_vector = query_embeddings[0]  # Get first embedding
            
            # Get stored embeddings from IPFS
            embeddings_data = self._ipfs_get_json(embeddings_cid)
            stored_embeddings = [np.array(emb) for emb in embeddings_data['embeddings']]
            
            # Calculate similarities
            similarities = [
                np.dot(query_vector, emb) / (np.linalg.norm(query_vector) * np.linalg.norm(emb))
                for emb in stored_embeddings
            ]
            
            # Get top k similar chunks
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            # Get manual content
            manual_data = self._ipfs_get_json(content_cid)
            
            # Return relevant chunks with scores
            results = [
                {
                    'chunk': manual_data['chunks'][idx]['text'],
                    'score': float(similarities[idx]),  # Convert to float for JSON serialization
                    'position': manual_data['chunks'][idx]['position']
                }
                for idx in top_indices
            ]
            
            return results
            
        except Exception as e:
            print(f"Detailed error: {str(e)}")  # Add detailed error logging
            raise Exception(f"Failed to query manual: {str(e)}")

    async def generate_response(
        self,
        query: str,
        relevant_chunks: List[Dict]
    ) -> str:
        """Generate response using LLM based on relevant manual sections."""
        try:
            # Combine relevant chunks
            context = "\n".join([chunk['chunk'] for chunk in relevant_chunks])
            
            # Generate response
            response = await openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical support assistant. Use the provided manual content to answer user queries accurately and concisely."
                    },
                    {
                        "role": "user",
                        "content": f"Based on these manual sections:\n{context}\n\nQuery: {query}"
                    }
                ]
            )
            
            return response.choices[0].message.content

            
        except Exception as e:
            raise Exception(f"Failed to generate response: {str(e)}")

