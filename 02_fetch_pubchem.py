import logging
import os
import time

import pandas as pd
import requests
from typing import Optional, Any
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import urllib.parse

def fetch_cid(drug_name: Any, smiles: Optional[str] = None) -> Optional[str]:
    """Fetch PubChem CID using drug name or SMILES."""
    # Ensure drug_name is a string and remove .0 if it's a float-string
    name_str = str(drug_name)
    name_clean = name_str.split('.')[0] if '.' in name_str else name_str
    
    # URL encode the name/CID
    name_encoded = urllib.parse.quote(name_clean)
    pug_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name_encoded}/cids/json"
    
    try:
        response = requests.get(pug_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return str(data['IdentifierList']['CID'][0])
    except Exception:
        pass

    # Fallback to SMILES
    if smiles:
        smiles_encoded = urllib.parse.quote(smiles)
        smiles_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{smiles_encoded}/cids/json"
        try:
            response = requests.get(smiles_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return str(data['IdentifierList']['CID'][0])
        except Exception:
            pass
            
    logger.warning(f"Failed to fetch CID for {drug_name}")
    return None

def fetch_description(cid: str) -> str:
    """Fetch pharmacological description for a given CID."""
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/description/json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'InformationList' in data and 'Information' in data['InformationList']:
                # Pick the first one that has a 'Description'
                for info in data['InformationList']['Information']:
                    if 'Description' in info:
                        return str(info['Description'])
    except Exception:
        logger.warning(f"Failed to fetch description for CID {cid}")
    return ""

def main() -> None:
    if not os.path.exists('cypd26_data.csv'):
        logger.error("Run 01_data_collection.py first.")
        return

    df = pd.read_csv('cypd26_data.csv')
    results = []

    logger.info("Fetching CIDs and descriptions from PubChem...")

    # Limit for demo purposes if needed
    # df = df.head(50)

    for _index, row in tqdm(df.iterrows(), total=len(df)):
        name = row['Drug_ID']
        smiles = row['Drug']
        y = row['Y']

        cid = fetch_cid(name, smiles)
        time.sleep(0.2) # Rate limiting

        description = ""
        if cid:
            description = fetch_description(cid)
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
