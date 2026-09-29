# src/load.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd
from sqlalchemy import create_engine
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, DATA_DIR


def load():
    # read transformed csv 
    csv_path = DATA_DIR / "processed" / "smartphones_cleaned.csv"
    df = pd.read_csv(csv_path)

    engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    df.to_sql("smartphones_cleaned", engine, if_exists="replace", index=False)

    print(f"Successfully loaded transformed data")


if __name__ == "__main__":
    load()