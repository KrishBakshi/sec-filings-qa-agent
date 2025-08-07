# step_0_fetch_metadata_by_ticker.py

from sec_api import QueryApi
import os
import dotenv
import pandas as pd
from time import sleep

# Load API Key
dotenv.load_dotenv()
query_api = QueryApi(api_key=os.getenv("SEC_API_KEY"))

# Tickers across various sectors
TICKERS = ["AAPL", "TSLA", "JPM", "PFE", "XOM", "AMZN", "BA", "NVDA", "DIS", "UNH"]
FILING_TYPES = ["10-K", "10-Q", "8-K", "DEF 14A"]
FILINGS_PER_PAIR = 20

all_filings = []

for ticker in TICKERS:
    for filing_type in FILING_TYPES:
        print(f"Fetching {FILINGS_PER_PAIR} filings: {ticker} - {filing_type}")

        query = f"ticker:{ticker} AND formType:{filing_type}"
        search_params = {
            "query": query,
            "from": "0",
            "size": FILINGS_PER_PAIR,
            "sort": [{"filedAt": {"order": "desc"}}],
        }

        try:
            response = query_api.get_filings(search_params)
            filings = response.get("filings", [])
            print(f"Found {len(filings)} filings for {ticker} - {filing_type}")

            all_filings.extend(filings)
            sleep(1.2)  # Rate limit protection

        except Exception as e:
            print(f"Error: {ticker} - {filing_type}: {e}")

# Save to CSV
if all_filings:
    df = pd.DataFrame.from_records(all_filings)
    df.to_csv("metadata.csv", index=False)
    print(f"\nTotal filings saved: {len(df)} → metadata.csv")
else:
    print("No filings fetched. Check your network or API key.")
