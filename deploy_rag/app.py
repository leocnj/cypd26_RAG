import logging
import os
from contextlib import asynccontextmanager
from typing import Any, List, Optional

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for shared resources
models = {}

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3

class QueryResponse(BaseModel):
    answer: str
    context: str
    provider: str

def bootstrap_efs_from_s3():
    """Download ChromaDB from S3 if the EFS mount is empty."""
    s3_bucket = os.environ.get("MIGRATION_S3_BUCKET")
    s3_prefix = os.environ.get("MIGRATION_S3_PREFIX", "migration/cyp2d6_knowledge_base")
    chroma_path = os.environ.get("CHROMA_PATH", "./chroma_db")

    if not s3_bucket:
        logger.info("No MIGRATION_S3_BUCKET set. Skipping bootstrap.")
        return

    # Check if directory is empty (usually it will contain at least a 'chroma.sqlite3' if initialized)
    is_empty = not os.path.exists(chroma_path) or not os.listdir(chroma_path)
    
    if is_empty:
        logger.info(f"EFS mount {chroma_path} is empty. Bootstrapping from s3://{s3_bucket}/{s3_prefix}...")
        try:
            import subprocess
            # Ensure the directory exists
            os.makedirs(chroma_path, exist_ok=True)
            # Use AWS CLI (pre-installed in Docker) to sync
            cmd = ["aws", "s3", "sync", f"s3://{s3_bucket}/{s3_prefix}", chroma_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("EFS Bootstrap successful.")
            else:
                logger.error(f"EFS Bootstrap failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Error during EFS Bootstrap: {str(e)}")
    else:
        logger.info(f"EFS mount {chroma_path} already contains data. Skipping bootstrap.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load environment variables
    load_dotenv()
    
    # 1. Bootstrap data from S3 to EFS if needed
    bootstrap_efs_from_s3()
    
    # 2. Initialize ChromaDB
    chroma_path = os.environ.get("CHROMA_PATH", "./chroma_db")
    logger.info(f"Connecting to ChromaDB at: {chroma_path}")
    
    try:
        chroma_client = chromadb.PersistentClient(path=chroma_path)
        model_name = "all-MiniLM-L6-v2"
        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )
        collection = chroma_client.get_collection(
            name="cyp2d6_knowledge_base", embedding_function=emb_fn
        )
        models["collection"] = collection
        models["count"] = collection.count()
        logger.info(f"Loaded RAG VectorDB with {models['count']} child chunk embeddings.")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {str(e)}")
        raise e

    yield
    # Clean up if needed
    models.clear()

app = FastAPI(title="CYP2D6 RAG API", lifespan=lifespan)

def get_rag_context(query_text: str, collection: Any, top_k: int = 3) -> str:
    """Core RAG retrieval logic ported from 04_cli_agent.py"""
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k
    )

    context_blocks: List[str] = []
    seen_drugs = set()

    for i in range(len(results['ids'][0])):
        meta = results['metadatas'][0][i]
        drug_id = str(meta.get('drug_id', 'Unknown'))

        if drug_id in seen_drugs:
            continue
        seen_drugs.add(drug_id)

        smiles = str(meta.get('smiles', ''))
        is_substrate = str(meta.get('is_substrate', ''))
        parent_doc = str(meta.get('parent_doc', ''))
        ecfp4_preview = (
            str(meta.get('ecfp4', ''))[:30] + '...'
            if meta.get('ecfp4') else ''
        )

        block = f"--- [{drug_id}] ---\n"
        block += f"SMILES: {smiles}\n"
        block += f"CYP2D6 Substrate: {'Yes' if is_substrate == '1' else 'No'}\n"
        block += f"ECFP4 (preview): {ecfp4_preview}\n"
        block += f"Pharmacology: {parent_doc}\n"
        context_blocks.append(block)

    return "\n".join(context_blocks)

def query_llm(provider: str, api_key: str, query_text: str, context: str) -> str:
    """Core LLM query logic ported from 04_cli_agent.py"""
    try:
        import requests
        prompt_intro = "You are an AI assistant for pharmaceutical drug discovery."
        prompt = f"""{prompt_intro} specializing in CYP2D6.
Use the following retrieved context to answer the user's question.
If you don't know the answer based on the context, say so.

Context:
{context}

Question: {query_text}
Answer:"""

        if provider == "gemini":
            gemini_model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{gemini_model}:generateContent?key={api_key}"
            )
            headers = {"Content-Type": "application/json"}
            data = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                res_json = response.json()
                if "candidates" in res_json and len(res_json["candidates"]) > 0:
                    return str(res_json["candidates"][0]["content"]["parts"][0]["text"])
                return f"Unexpected Gemini response: {res_json}"
            else:
                logger.error(f"Gemini API Error: {response.text}")
                return f"LLM Error: {response.status_code}"

        else: # default to openai
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
            openai_url = "https://api.openai.com/v1/chat/completions"
            response = requests.post(
                openai_url, headers=headers, json=data, timeout=30
            )
            if response.status_code == 200:
                return str(response.json()['choices'][0]['message']['content'])
            else:
                logger.error(f"OpenAI API Error: {response.text}")
                return f"LLM Error: {response.status_code}"
    except Exception as e:
        logger.exception("Exception occurred during LLM query")
        return f"Error connecting to LLM: {str(e)}"

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "vector_db_count": models.get("count", 0),
        "chroma_path": os.environ.get("CHROMA_PATH", "./chroma_db")
    }

@app.post("/query", response_model=QueryResponse)
async def run_query(request: QueryRequest):
    collection = models.get("collection")
    if not collection:
        raise HTTPException(status_code=500, detail="Vector Database not initialized")

    # 1. Retrieval
    context = get_rag_context(request.query, collection, top_k=request.top_k)

    # 2. Preparation for Generation
    provider = os.environ.get("LLM_PROVIDER", "openai").lower()
    if provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY", "")
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "")

    if not api_key:
        return QueryResponse(
            answer="[Notice] API Key not found. Running in Retrieval-only mode.",
            context=context,
            provider="none"
        )

    # 3. Generation
    answer = query_llm(provider, api_key, request.query, context)
    
    return QueryResponse(
        answer=answer,
        context=context,
        provider=provider
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
