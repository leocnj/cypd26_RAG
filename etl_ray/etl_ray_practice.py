import ray
import s3fs
import pyarrow.fs
import pyarrow.csv
import os
import pandas as pd

# Set environment variable to suppress Mac memory limit warning if needed
os.environ["RAY_ENABLE_MAC_LARGE_OBJECT_STORE"] = "1"

# 1. Initialize local Ray cluster
ray.init()

# Enable rich progress UI
ctx = ray.data.DataContext.get_current()
ctx.enable_rich_progress_bars = True
ctx.use_ray_tqdm = False

# 2. Setup access to the public bucket (anonymous)
fs = s3fs.S3FileSystem(anon=True, client_kwargs={'region_name': 'us-east-1'})

# 3. Read the massive 2023 NOAA CSV dataset (approx 1.3GB)
s3_input_path = "noaa-ghcn-pds/csv/by_year/2023.csv"
print(f"Reading from: s3://{s3_input_path}")

# Let Ray/PyArrow discover the schema automatically from the CSV header
dataset = ray.data.read_csv(
    s3_input_path, 
    filesystem=fs
)

# 4. Define our ETL function
def my_etl_transform(df):
    # Ensure DATA_VALUE is numeric before comparison
    df["DATA_VALUE"] = pd.to_numeric(df["DATA_VALUE"], errors="coerce")
    # Filter for Max Temperature (TMAX) > 30 degrees Celsius (300 in tenths)
    filtered_df = df[(df["ELEMENT"] == "TMAX") & (df["DATA_VALUE"] > 300)]
    return filtered_df

# 5. Apply the transformation
processed_ds = dataset.map_batches(my_etl_transform, batch_format="pandas")

# Show one output record
print("\n--- Example Processed Record (High Temp Reading) ---")
processed_ds.show(1)
print("--------------------------------\n")

# 6. Write to YOUR bucket using your configured AWS credentials
s3_output_path = "s3://my-ray-practice-bucket-20260313/processed-noaa-high-temp/"
print(f"Writing to: {s3_output_path}")

processed_ds.write_parquet(s3_output_path)
print("Done!")
