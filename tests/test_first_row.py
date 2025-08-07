#!/usr/bin/env python3
"""
Simple test script for the first row from metadata.csv
Saves output to current directory (./) for testing
"""
import pandas as pd
import prd

def main():
    # Temporarily change output directory to current directory for testing
    original_dir = prd.CLEANED_DIR
    prd.CLEANED_DIR = "./"  # Save to current directory for testing
    
    # Load metadata and get first row
    df = pd.read_csv("metadata.csv")
    first_row = df.iloc[0]
    
    print("First row from metadata.csv:")
    print(f"Ticker: {first_row['ticker']}")
    print(f"Form Type: {first_row['formType']}")
    print(f"Company: {first_row['companyName']}")
    print(f"Accession No: {first_row['accessionNo']}")
    print(f"Filed At: {first_row['filedAt']}")
    print(f"TXT URL: {first_row['linkToTxt']}")
    
    print(f"\nProcessing this filing... (saving to {prd.CLEANED_DIR})")
    try:
        prd.download_and_clean(first_row)
        print("✅ Done! Check current directory for the .md file")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Restore original directory setting
        prd.CLEANED_DIR = original_dir

if __name__ == "__main__":
    main() 