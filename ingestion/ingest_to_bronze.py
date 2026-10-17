import os
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import boto3
import pandas as pd
from botocore.client import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()  # reads passwords from your .env file

BUCKET = "supplychain-data"
SOURCE_DIR = Path("data/sample")
ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT,
    aws_access_key_id=os.environ["MINIO_ROOT_USER"],
    aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)


def ensure_bucket():
    """Create the bucket if it doesn't exist yet."""
    try:
        s3.head_bucket(Bucket=BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=BUCKET)
        print(f"Created bucket {BUCKET}")


def read_raw(path: Path) -> pd.DataFrame:
    """Read a file with NO type guessing: everything stays as text."""
    if path.suffix == ".csv":
        return pd.read_csv(path, dtype="string")
    return pd.read_json(path, dtype=False, convert_dates=False).astype("string")


def main():
    ensure_bucket()

    now = datetime.now(timezone.utc)
    run_date = now.strftime("%Y-%m-%d")
    ingested_at = now.isoformat()
    batch_id = uuid.uuid4().hex[:8]

    files = sorted(list(SOURCE_DIR.glob("*.csv")) + list(SOURCE_DIR.glob("*.json")))
    if not files:
        raise SystemExit("No files found in data/sample. Run data/generate_data.py first.")

    print(f"Batch {batch_id} | {len(files)} files\n")
    for path in files:
        df = read_raw(path)

        # Metadata columns: the "paper trail" for every row
        df["_source_file"] = path.name
        df["_ingested_at"] = ingested_at
        df["_batch_id"] = batch_id

        buffer = BytesIO()
        df.to_parquet(buffer, index=False)

        key = f"bronze/{path.stem}/ingest_date={run_date}/{path.stem}.parquet"
        s3.put_object(Bucket=BUCKET, Key=key, Body=buffer.getvalue())
        print(f"{path.name:18} {len(df):>7,} rows  ->  {key}")

    print("\nDone.")


if __name__ == "__main__":
    main()