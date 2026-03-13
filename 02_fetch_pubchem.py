import pandas as pd
import requests
import time
import os
from tqdm import tqdm

def get_cid_by_name(name):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/cids/JSON"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data['IdentifierList']['CID'][0]
    except Exception as e:
        pass
    return None

def get_description_by_cid(cid):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/description/JSON"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'InformationList' in data and 'Information' in data['InformationList']:
                # The description can be in multiple entries. Pick the first one that has a 'Description'
                for info in data['InformationList']['Information']:
                    if 'Description' in info:
                        return info['Description']
    except Exception as e:
        pass
    return ""

def main():
    if not os.path.exists('cyp2d6_substrate.csv'):
        print("Run 01_data_collection.py first.")
        return

    df = pd.read_csv('cyp2d6_substrate.csv')
    results = []
    
    print("Fetching CIDs and descriptions from PubChem (limited to first 50 for faster demo)...")
    # df = df.head(50)
    
    # For a quicker RAG demo start, we can limit to the first 50 compounds or fetch all.
    for index, row in tqdm(df.iterrows(), total=len(df)):
        name = row['Drug_ID']
        smiles = row['Drug']
        y = row['Y']
        
        cid = get_cid_by_name(name)
        time.sleep(0.2) # Rate limiting 5 requests per sec
        
        description = ""
        if cid:
            description = get_description_by_cid(cid)
            time.sleep(0.2)
            
        results.append({
            'Drug_ID': name,
            'SMILES': smiles,
            'Y': y,
            'CID': cid,
            'Description': description
        })
        
    out_df = pd.DataFrame(results)
    out_df.to_csv('cyp2d6_with_pubchem.csv', index=False)
    
    # Check how many have missing descriptions
    missing = out_df['Description'].isna() | (out_df['Description'] == "")
    print(f"Total processed: {len(out_df)}")
    print(f"Missing descriptions: {missing.sum()}")
    print("Saved to cyp2d6_with_pubchem.csv")

if __name__ == '__main__':
    main()
