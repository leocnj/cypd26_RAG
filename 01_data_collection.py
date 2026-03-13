import logging

from tdc.single_pred import ADME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_tdc_data() -> None:
    logger.info("Downloading CYP2D6 substrate data from TDC...")
    data = ADME(name='cyp2d6_substrate_carbonmangels')
    df = data.get_data()
    df.to_csv('cypd26_data.csv', index=False)
    logger.info(f"Saved {len(df)} records to cypd26_data.csv")

if __name__ == '__main__':
    download_tdc_data()
