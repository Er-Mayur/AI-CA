import chromadb
from chromadb.utils import embedding_functions
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
import uuid
import os
import httpx
from typing import List, Dict, Any, Optional
from utils.ollama_client import OLLAMA_BASE_URL, OLLAMA_MODEL


class OllamaEmbeddingFunction(EmbeddingFunction):
    """Custom embedding function for Ollama (compatible with chromadb 0.4.x)"""
    
    def __init__(self, url: str, model_name: str):
        self.url = url
        self.model_name = model_name
    
    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            try:
                response = httpx.post(
                    self.url,
                    json={"model": self.model_name, "prompt": text},
                    timeout=60.0
                )
                if response.status_code == 200:
                    data = response.json()
                    embeddings.append(data.get("embedding", []))
                else:
                    # Fallback: return empty embedding
                    print(f"Ollama embedding error: {response.status_code}")
                    embeddings.append([0.0] * 768)
            except Exception as e:
                print(f"Ollama embedding exception: {e}")
                embeddings.append([0.0] * 768)
        return embeddings


# 1. Setup ChromaDB with Ollama Embeddings
ollama_ef = OllamaEmbeddingFunction(
    url=f"{OLLAMA_BASE_URL}/api/embeddings",
    model_name=OLLAMA_MODEL
)

# Persistent storage in backend/chroma_db folder
result_storage = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
os.makedirs(result_storage, exist_ok=True)
client = chromadb.PersistentClient(path=result_storage)

# 2. Collections
# Tax Rules: General knowledge (no user specific, maybe year specific for rules changing)
try:
    rules_collection = client.get_or_create_collection(
        name="tax_rules", 
        embedding_function=ollama_ef
    )
except Exception as e:
    # Handle cases where get_or_create might fail due to dimensionality mismatch if model changed
    print(f"Error creating rules collection: {e}")
    rules_collection = client.get_collection(name="tax_rules", embedding_function=ollama_ef)

# User Data: Highly sensitive, must be filtered by User ID and Year
try:
    user_data_collection = client.get_or_create_collection(
        name="user_data", 
        embedding_function=ollama_ef
    )
except Exception as e:
    print(f"Error creating user_data collection: {e}")
    user_data_collection = client.get_collection(name="user_data", embedding_function=ollama_ef)

class RAGEngine:
    def __init__(self):
        self.rules = rules_collection
        self.user_data = user_data_collection

    def index_user_document(self, user_id: int, doc_type: str, financial_year: str, data: Dict[str, Any]):
        """
        Index a user document (Form 16, AIS etc) with strict metadata for the specific Financial Year.
        """
        if not financial_year:
            financial_year = "unknown"

        chunks = []
        metadatas = []
        ids = []

        # Helper to flatten JSON into readable text chunks
        def process_json(obj, parent_key=''):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    new_key = f"{parent_key} {k}" if parent_key else k
                    process_json(v, new_key)
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    process_json(v, f"{parent_key}[{i}]")
            else:
                # This is a leaf value (int, float, string)
                # Create a semantic sentence: "Form 16 (2024-25) - Gross Salary: 500000"
                clean_key = parent_key.replace('_', ' ').strip().title()
                # Skip if value is null or empty
                if obj is None or obj == "":
                    return
                    
                text = f"{doc_type} ({financial_year}) - {clean_key}: {obj}"
                
                chunks.append(text)
                
                # METADATA IS KEY: This allows us to filter later
                metadatas.append({
                    "user_id": user_id,
                    "year": financial_year,
                    "doc_type": doc_type,
                    "field": clean_key
                })
                ids.append(f"{user_id}_{financial_year}_{doc_type.replace(' ', '_')}_{str(uuid.uuid4())}")

        process_json(data)

        if chunks:
            # Clear previous entries for this specific document to avoid duplicates
            try:
                # Note: ChromaDB delete filter structure:
                self.user_data.delete(where={
                    "$and": [
                        {"user_id": user_id},
                        {"year": financial_year},
                        {"doc_type": doc_type}
                    ]
                })
                print(f"Cleared previous index for {doc_type} FY {financial_year}")
            except Exception as e:
                print(f"Error clearing previous index: {e}")

            # Add new chunks
            try:
                self.user_data.add(
                    documents=chunks,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"Indexed {len(chunks)} chunks for {doc_type} FY {financial_year}")
            except Exception as e:
                print(f"Error adding to index: {e}")

    def search_context(self, query: str, user_id: int, financial_year: Optional[str] = None) -> str:
        """
        Retrieve context strictly filtering by Financial Year if provided.
        """
        context_parts = []

        # 1. Fetch relevant generic tax rules
        try:
            rule_results = self.rules.query(
                query_texts=[query],
                n_results=2
            )
            if rule_results['documents'] and rule_results['documents'][0]:
                context_parts.append("RELEVANT TAX RULES:")
                context_parts.extend(rule_results['documents'][0])
        except Exception as e:
            print(f"Error querying rules: {e}")

        # 2. Fetch User Data with Filter
        # If financial_year is specified, we ONLY look at that year's docs
        where_filter = {"user_id": user_id}
        
        if financial_year:
            where_filter = {
                "$and": [
                    {"user_id": user_id},
                    {"year": financial_year}
                ]
            }
            header = f"USER DATA (FY {financial_year}):"
        else:
            header = "USER DATA (ALL YEARS):"

        try:
            user_results = self.user_data.query(
                query_texts=[query],
                n_results=5,
                where=where_filter
            )

            if user_results['documents'] and user_results['documents'][0]:
                context_parts.append(f"\n{header}")
                context_parts.extend(user_results['documents'][0])
        except Exception as e:
            print(f"Error querying user data: {e}")

        return "\n\n".join(context_parts)
