import os
import sys
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mysql.connector
import pandas as pd
from config import DB_HOST, DB_USER, DB_PASS, DB_NAME, DATA_DIR


def extract():
    # Connect to RDS
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
    )

    try:
        df = pd.read_sql_query("SELECT * FROM smartphones_raw", conn) #type: ignore
    finally:
        conn.close()

    # Ensure output dir exists
    raw_dir = DATA_DIR / "raw"
    os.makedirs(raw_dir, exist_ok=True)

    # Save
    output_path = raw_dir / "smartphones.csv"
    df.to_csv(output_path, index=False)

    print(f"✓ Extracted {len(df)} rows → {output_path}")


if __name__ == "__main__":
    extract()