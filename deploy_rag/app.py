import logging
import os
import sys

# CRITICAL: Early logging to catch import errors
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info("Container starting up. Python version: %s", sys.version)

import threading
from contextlib import asynccontextmanager
from typing import Any, List, Optional

try:
    import chromadb
    from chromadb.utils import embedding_functions
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from pydantic import BaseModel
    import requests
    from dotenv import load_dotenv
    logger.info("Successfully imported core dependencies.")
except Exception as e:
    logger.error("Failed to import dependencies: %s", str(e))
    raise e

# Global variables
models = {}

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3

class QueryResponse(BaseModel):
    answer: str
    context: str
    provider: str

def bootstrap_efs_from_s3():
    """Background task to sync data from S3."""
    s3_bucket = os.environ.get("MIGRATION_S3_BUCKET")
    s3_prefix = os.environ.get("MIGRATION_S3_PREFIX", "migration/cyp2d6_knowledge_base")
    chroma_path = os.environ.get("CHROMA_PATH", "/app/chroma_db")

    if not s3_bucket:
        logger.info("No MIGRATION_S3_BUCKET set. Skipping bootstrap.")
        return

    logger.info(f"Background Sync: Checking {chroma_path} for data...")
    is_empty = not os.path.exists(chroma_path) or not os.listdir(chroma_path)
    
    if is_empty:
        logger.info(f"Syncing from s3://{s3_bucket}/{s3_prefix}...")
        try:
            import subprocess
            os.makedirs(chroma_path, exist_ok=True)
            cmd = ["aws", "s3", "sync", f"s3://{s3_bucket}/{s3_prefix}", chroma_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("S3 Sync successful.")
                # After sync, reload the collection count
                try:
                    chroma_client = chromadb.PersistentClient(path=chroma_path)
                    collection = chroma_client.get_collection(name="cyp2d6_knowledge_base")
                    models["collection"] = collection
                    models["count"] = collection.count()
                    logger.info(f"Refreshed VectorDB with {models['count']} records.")
                except:
                    pass
            else:
                logger.error(f"S3 Sync failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Error during S3 Sync: {str(e)}")
    else:
        logger.info(f"Data already present at {chroma_path}.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    
    # 1. Start S3 sync in a SEPARATE THREAD so it doesn't block startup
    threading.Thread(target=bootstrap_efs_from_s3, daemon=True).start()
    
    # 2. Try to initialize existing ChromaDB (if any)
    chroma_path = os.environ.get("CHROMA_PATH", "/app/chroma_db")
    if os.path.exists(chroma_path) and os.listdir(chroma_path):
        try:
            chroma_client = chromadb.PersistentClient(path=chroma_path)
            model_name = "all-MiniLM-L6-v2"
            emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
            collection = chroma_client.get_collection(name="cyp2d6_knowledge_base", embedding_function=emb_fn)
            models["collection"] = collection
            models["count"] = collection.count()
            logger.info(f"Initialized with existing data: {models['count']} records.")
        except Exception as e:
            logger.warning(f"Initial DB connect failed (might still be syncing): {e}")

    yield
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
            api_version = os.environ.get("GEMINI_API_VERSION", "v1beta")
            url = (
                f"https://generativelanguage.googleapis.com/{api_version}/models/"
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
