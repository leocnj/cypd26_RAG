import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

def generate_ecfp4(smiles):
    if pd.isna(smiles) or not isinstance(smiles, str):
        return ""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            return ""
        # Generate ECFP4 fingerprint (radius 2, 2048 bits)
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
        return fp.ToBitString()
    except:
        return ""

def build_db():
    if not os.path.exists('cyp2d6_with_pubchem.csv'):
        print("Run 02_fetch_pubchem.py first.")
        return

    df = pd.read_csv('cyp2d6_with_pubchem.csv')
    df['Description'] = df['Description'].fillna('')
    
    print("Initializing ChromaDB and Local Embedding Model...")
    
    # 1. Initialize ChromaDB
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    # 2. Setup Embedding function (Sentence-Transformers local model)
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    collection = chroma_client.get_or_create_collection(
        name="cyp2d6_knowledge_base",
        embedding_function=emb_fn,
        metadata={"hnsw:space": "cosine"}
    )
    
    # 3. Text Splitter for Parent-Child Relationship
    # We will split long pharmacological descriptions into smaller chunks (children), 
    # but store the entire description in metadata as the "parent"
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    
    print("Building Vector DB with Parent-Child chunks and ECFP4...")
    
    docs = []
    metadatas = []
    ids = []
    
    chunk_counter = 0
    
    for idx, row in df.iterrows():
        drug_id = str(row['Drug_ID'])
        smiles = str(row['SMILES'])
        y = str(row['Y'])
        desc = str(row['Description'])
        
        # Calculate fingerprint
        fp = generate_ecfp4(smiles)
        
        # The parent document is the full description. 
        # By adding `parent_doc` to metadata, we enable Parent-Child Retrieval.
        base_meta = {
            "drug_id": drug_id,
            "smiles": smiles,
            "is_substrate": y,
            "ecfp4": fp,
            "parent_doc": desc
        }
        
        if len(desc.strip()) > 0:
            chunks = text_splitter.split_text(desc)
            for chunk_idx, chunk in enumerate(chunks):
                chunk_id = f"{drug_id}_chunk_{chunk_idx}"
                meta = base_meta.copy()
                meta["chunk_index"] = chunk_idx
                meta["is_child"] = True
                
                docs.append(chunk)
                metadatas.append(meta)
                ids.append(chunk_id)
                chunk_counter += 1
        else:
            # If there's no pharmacology description, we just add the drug name and info
            chunk_id = f"{drug_id}_chunk_0"
            meta = base_meta.copy()
            meta["chunk_index"] = 0
            meta["is_child"] = True
            
            docs.append(f"Drug {drug_id}. SMILES: {smiles}. No pharmacological description available.")
            metadatas.append(meta)
            ids.append(chunk_id)
            chunk_counter += 1

    # Batch insert to avoid huge payload size issues
    print(f"Prepared {chunk_counter} child chunks. Inserting into ChromaDB in batches...")
    batch_size = 100
    for i in range(0, len(docs), batch_size):
        collection.upsert(
            documents=docs[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
        
    print(f"Insertion complete. Vector DB is ready with Parent-Child retrieval capability.")

if __name__ == '__main__':
    build_db()
