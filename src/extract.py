import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# ---------------------------------------------------------------------
import mysql.connector
import pandas as pd
from config import DB_HOST, DB_USER, DB_PASS, DB_NAME, DATA_DIR

# connect to aws database server
conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME,
)

# Extract raw dataset from server
df = pd.read_sql_query("SELECT * FROM smartphones_raw", conn)
conn.close()

# Save desired path 
raw_dir = DATA_DIR / "raw"
os.makedirs(raw_dir, exist_ok=True)
df.to_csv(raw_dir / "smartphones.csv", index=False)

print(f"Extracted {len(df)} rows")