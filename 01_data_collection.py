import pandas as pd
from tdc.single_pred import ADME

def download_tdc_data():
    print("Downloading TDC CYP2D6 Substrate dataset...")
    data = ADME(name = 'CYP2D6_Substrate_CarbonMangels')
    df = data.get_data()
    print(df.head())
    print(f"\nTotal molecules: {len(df)}")
    df.to_csv('cyp2d6_substrate.csv', index=False)
    print("Saved to cyp2d6_substrate.csv")

if __name__ == '__main__':
    download_tdc_data()
