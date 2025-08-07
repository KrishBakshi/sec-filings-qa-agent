#!/usr/bin/env python3
"""
Script to add YAML frontmatter with metadata to cleaned markdown files.
This matches SEC filings with their metadata from metadata.csv.
"""
import pandas as pd
import os
import yaml
from pathlib import Path
import re
from urllib.parse import urlparse

# Paths
METADATA_CSV = "metadata.csv"
CLEANED_DIR = "cleaned_filings"

def extract_accession_from_filename(filename):
    """Extract accession number from filename like sec_Archives_edgar_data_1045810_000104581022000067_0001045810-22-000067.txt.md"""
    # Pattern to match accession number (typically the last part before .txt.md)
    match = re.search(r'_([0-9]+-[0-9]+-[0-9]+)\.txt\.md$', filename)
    if match:
        return match.group(1)
    return None

def extract_accession_from_url(url):
    """Extract accession number from SEC URL"""
    if not url:
        return None
    # Parse URL and extract accession number
    parsed = urlparse(url)
    path_parts = parsed.path.split('/')
    for part in path_parts:
        if re.match(r'[0-9]+-[0-9]+-[0-9]+', part):
            return part
    return None

def create_metadata_dict(row):
    """Create metadata dictionary from CSV row"""
    metadata = {}
    
    # Core fields that should be in your retrieval
    if 'ticker' in row and pd.notna(row['ticker']):
        metadata['ticker'] = row['ticker']
    
    if 'formType' in row and pd.notna(row['formType']):
        metadata['filing_type'] = row['formType']
    elif 'filingType' in row and pd.notna(row['filingType']):
        metadata['filing_type'] = row['filingType']
    
    if 'filedAt' in row and pd.notna(row['filedAt']):
        metadata['filing_date'] = row['filedAt']
    elif 'filingDate' in row and pd.notna(row['filingDate']):
        metadata['filing_date'] = row['filingDate']
    
    if 'accessionNo' in row and pd.notna(row['accessionNo']):
        metadata['accession_number'] = row['accessionNo']
    
    # Additional useful fields
    if 'companyName' in row and pd.notna(row['companyName']):
        metadata['company_name'] = row['companyName']
    elif 'companyNameLong' in row and pd.notna(row['companyNameLong']):
        metadata['company_name'] = row['companyNameLong']
    
    if 'cik' in row and pd.notna(row['cik']):
        metadata['cik'] = row['cik']
    
    # Try to determine section (for now, use filing type as section)
    metadata['section'] = metadata.get('filing_type', 'Unknown')
    
    return metadata

def add_frontmatter_to_file(filepath, metadata):
    """Add YAML frontmatter to a markdown file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file already has frontmatter
        if content.startswith('---'):
            print(f"⚠️  {filepath} already has frontmatter, skipping")
            return False
        
        # Create YAML frontmatter
        yaml_header = yaml.dump(metadata, default_flow_style=False, sort_keys=True)
        
        # Combine frontmatter with content
        new_content = f"---\n{yaml_header}---\n\n{content}"
        
        # Write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Added metadata to: {os.path.basename(filepath)}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

def main():
    # Load metadata CSV
    if not os.path.exists(METADATA_CSV):
        print(f"❌ {METADATA_CSV} not found!")
        return
    
    print(f"📄 Loading metadata from {METADATA_CSV}")
    df = pd.read_csv(METADATA_CSV)
    print(f"📊 Found {len(df)} metadata records")
    
    # Get list of markdown files
    markdown_files = list(Path(CLEANED_DIR).glob("*.md"))
    print(f"📂 Found {len(markdown_files)} markdown files")
    
    matched = 0
    processed = 0
    
    # Create lookup dictionary by accession number
    accession_lookup = {}
    for idx, row in df.iterrows():
        acc_num = row.get('accessionNo')
        if pd.notna(acc_num):
            accession_lookup[acc_num] = row
    
    print(f"🔍 Created lookup for {len(accession_lookup)} accession numbers")
    
    # Process each markdown file
    for md_file in markdown_files:
        filename = md_file.name
        
        # Extract accession number from filename
        accession = extract_accession_from_filename(filename)
        
        if not accession:
            print(f"⚠️  Could not extract accession number from: {filename}")
            continue
        
        # Look up metadata
        if accession in accession_lookup:
            row = accession_lookup[accession]
            metadata = create_metadata_dict(row)
            
            if metadata:
                success = add_frontmatter_to_file(md_file, metadata)
                if success:
                    processed += 1
                matched += 1
            else:
                print(f"⚠️  No valid metadata for: {filename}")
        else:
            print(f"⚠️  No metadata found for accession: {accession} (file: {filename})")
    
    print(f"\n📊 Summary:")
    print(f"   - Total markdown files: {len(markdown_files)}")
    print(f"   - Matched with metadata: {matched}")
    print(f"   - Successfully processed: {processed}")
    print(f"   - Metadata records: {len(df)}")

if __name__ == "__main__":
    main() 