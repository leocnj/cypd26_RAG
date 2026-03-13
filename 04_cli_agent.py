import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from colorama import init, Fore, Style

def get_rag_context(query_text, collection, top_k=3):
    """
    Search ChromaDB using Sentence-Transformers and reconstruct the Parent Document 
    from the retrieved child chunks.
    """
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k
    )
    
    context_blocks = []
    # Deduplicate parent documents since multiple child chunks might belong to the same parent
    seen_drugs = set()
    
    for i in range(len(results['ids'][0])):
        meta = results['metadatas'][0][i]
        drug_id = meta.get('drug_id', 'Unknown')
        
        if drug_id in seen_drugs:
            continue
        seen_drugs.add(drug_id)
        
        smiles = meta.get('smiles', '')
        is_substrate = meta.get('is_substrate', '')
        parent_doc = meta.get('parent_doc', '')
        ecfp4_preview = meta.get('ecfp4', '')[:30] + '...' if meta.get('ecfp4') else ''
        
        block = f"--- [{drug_id}] ---\n"
        block += f"SMILES: {smiles}\n"
        block += f"CYP2D6 Substrate: {'Yes' if is_substrate == '1' else 'No'}\n"
        block += f"ECFP4 (preview): {ecfp4_preview}\n"
        block += f"Pharmacology: {parent_doc}\n"
        context_blocks.append(block)
        
    return "\n".join(context_blocks)

def query_llm(provider, api_key, query_text, context):
    try:
        import requests
        prompt = f"""You are an AI assistant for pharmaceutical drug discovery, specializing in CYP2D6.
Use the following retrieved context to answer the user's question. If you don't know the answer based on the context, say so.

Context:
{context}

Question: {query_text}
Answer:"""

        if provider == "gemini":
            gemini_model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            data = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                res_json = response.json()
                if "candidates" in res_json and len(res_json["candidates"]) > 0:
                    return res_json["candidates"][0]["content"]["parts"][0]["text"]
                return f"Unexpected Gemini response: {res_json}"
            else:
                return f"LLM Error: {response.text}"
                
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
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"LLM Error: {response.text}"
    except Exception as e:
        return f"Error connecting to LLM: {str(e)}"

def main():
    # Initialize colorama for cross-platform color support
    init(autoreset=True)
    
    print(Fore.CYAN + "="*50)
    print(Fore.CYAN + " CYP2D6 Drug Discovery Agent (CLI)")
    print(Fore.CYAN + "="*50)
    
    # Load environment variables
    load_dotenv()
    
    
    # Initialize ChromaDB
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = chroma_client.get_collection(name="cyp2d6_knowledge_base", embedding_function=emb_fn)
    
    count = collection.count()
    print(f"[*] Loaded RAG VectorDB with {count} child chunk embeddings.")
    
    provider = os.environ.get("LLM_PROVIDER", "openai").lower()
    if provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY", "")
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        
    if not api_key:
        print(f"\n[Warning] {provider.upper()} API Key not found in .env.")
        print("[*] Running in Retrieval-Only mode.")
    else:
        print(f"[*] LLM integration enabled using {provider.upper()}!")
    
    print(Fore.CYAN + "\n" + "="*50)
    print(Fore.CYAN + "Type your query below or 'exit' to quit.")
    
    while True:
        query = input(f"\n{Fore.GREEN}User > {Style.RESET_ALL}").strip()
        if query.lower() in ['exit', 'quit']:
            break
        if not query:
            continue
            
        print(Fore.YELLOW + "\n[Agent] Searching Knowledge Base...")
        context = get_rag_context(query, collection, top_k=3)
        
        print(Fore.BLUE + "\n--- RAG Retrieved Context ---")
        print(Fore.BLUE + context)
        print(Fore.BLUE + "-----------------------------\n")
        
        if api_key:
            print(Fore.YELLOW + f"[Agent] Generating Answer with {provider.upper()}...")
            answer = query_llm(provider, api_key, query, context)
            print(Fore.GREEN + f"\n[Agent Output]\n{answer}")

if __name__ == "__main__":
    main()
