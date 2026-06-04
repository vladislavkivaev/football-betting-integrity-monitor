"""
load_to_rds.py
--------------
Loads data/processed/master_enriched.csv into the Spiced PostgreSQL database,
into the user's personal schema, as the raw landing table for the dbt pipeline.

Run from the repo root:  python scripts/load_to_rds.py

Credentials are read from a local .env file (never committed). Required keys:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_SCHEMA
"""

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# --- config -----------------------------------------------------------------
CSV_PATH = Path("data/processed/master_enriched.csv")
RAW_TABLE = "matches_raw"          # the untouched landing table dbt reads from
EXPECTED_ROWS = 8915               # sanity check from your cleaning stage

# --- load credentials -------------------------------------------------------
load_dotenv()  # reads .env from the current working directory

required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_SCHEMA"]
missing = [k for k in required if not os.getenv(k)]
if missing:
    sys.exit(f"Missing env vars: {', '.join(missing)}. Fill them in your .env file.")

host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = quote_plus(os.getenv("DB_PASSWORD"))  # url-encode in case of @ : / etc.
schema = os.getenv("DB_SCHEMA")

conn_str = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
engine = create_engine(conn_str)

# --- step 1: test the connection BEFORE touching the data -------------------
try:
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version();")).scalar()
    print(f"✅ Connected. Server: {version.split(',')[0]}")
except Exception as e:
    sys.exit(f"❌ Connection failed: {e}")

# --- step 2: read and validate the CSV --------------------------------------
if not CSV_PATH.exists():
    sys.exit(f"❌ CSV not found at {CSV_PATH}. Run this from the repo root.")

df = pd.read_csv(CSV_PATH)
print(f"📄 Read {len(df):,} rows × {df.shape[1]} columns from {CSV_PATH.name}")

if len(df) != EXPECTED_ROWS:
    print(f"⚠️  Expected {EXPECTED_ROWS:,} rows but got {len(df):,}. Check before continuing.")


# --- step 3: load (replace so the script is re-runnable) --------------------
df.to_sql(
    RAW_TABLE,
    engine,
    schema=schema,
    if_exists="replace",   # idempotent: re-running gives the same clean state
    index=False,
    chunksize=1000,
    method="multi",        # batches inserts; much faster than row-by-row
)
print(f"⬆️  Loaded into {schema}.{RAW_TABLE}")

# --- step 4: verify the round-trip ------------------------------------------
with engine.connect() as conn:
    count = conn.execute(
        text(f'SELECT COUNT(*) FROM "{schema}"."{RAW_TABLE}";')
    ).scalar()

if count == len(df):
    print(f"✅ Verified: {count:,} rows in {schema}.{RAW_TABLE}. Done.")
else:
    print(f"⚠️  Row mismatch: CSV had {len(df):,}, table has {count:,}.")