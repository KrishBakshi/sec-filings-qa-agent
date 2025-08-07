import pandas as pd
import requests
import os
import asyncio
import re
from pathlib import Path
from bs4 import BeautifulSoup
import hashlib
from urllib.parse import urlparse
from datetime import datetime
import yaml
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# Paths
METADATA_CSV = "metadata.csv"
# DOWNLOAD_DIR = "raw_filings"
CLEANED_DIR = "cleaned_filings"
# Path(DOWNLOAD_DIR).mkdir(exist_ok=True)
Path(CLEANED_DIR).mkdir(exist_ok=True)

# Load metadata
df = pd.read_csv(METADATA_CSV)

# Track failed downloads
failed = []

def get_filename_from_metadata(row):
    """Create unique filename based on accession number."""
    acc_num = row.get("accessionNo", "unknown").replace("/", "-")
    ticker = row.get("ticker", "unknown")
    form = row.get("formType", "form")
    return f"{ticker}_{form}_{acc_num}"

def create_metadata_frontmatter(row):
    """Create YAML frontmatter from metadata row"""
    metadata = {}
    
    # Core fields for retrieval system
    if 'ticker' in row and pd.notna(row['ticker']):
        metadata['ticker'] = row['ticker']
    
    if 'formType' in row and pd.notna(row['formType']):
        metadata['filing_type'] = row['formType']
    
    if 'filedAt' in row and pd.notna(row['filedAt']):
        metadata['filing_date'] = row['filedAt']
    
    if 'accessionNo' in row and pd.notna(row['accessionNo']):
        metadata['accession_number'] = row['accessionNo']
    
    # Additional useful fields
    if 'companyName' in row and pd.notna(row['companyName']):
        metadata['company_name'] = row['companyName']
    elif 'companyNameLong' in row and pd.notna(row['companyNameLong']):
        metadata['company_name'] = row['companyNameLong']
    
    if 'cik' in row and pd.notna(row['cik']):
        metadata['cik'] = int(row['cik'])  # Convert to int to avoid numpy scalar issues
    
    # Use filing type as section
    metadata['section'] = metadata.get('filing_type', 'Unknown')
    
    return metadata

def add_frontmatter_to_content(content, metadata):
    """Add YAML frontmatter to content"""
    if not metadata:
        return content
    
    yaml_header = yaml.dump(metadata, default_flow_style=False, sort_keys=True)
    return f"---\n{yaml_header}---\n\n{content}"

def extract_clean_text_from_html(html_content):
    """Extract clean text from HTML content using the data_preprocess.py approach"""
    soup = BeautifulSoup(html_content, "lxml")
    
    body = soup.find("body")
    if not body:
        # If no body tag, use the entire soup
        body = soup
    
    # Remove all <script> and <style> tags
    for tag in body(["script", "style"]):
        tag.decompose()
    
    # Remove hidden content
    for tag in body.find_all(style=lambda s: s and "display:none" in s):
        tag.decompose()
    
    # Remove all XBRL/XML tags
    for tag in body.find_all(True):
        if tag.name and (tag.name.startswith('xbrl') or tag.name.startswith('ix')):
            tag.decompose()
    
    # Return cleaned text
    return body.get_text(separator="\n", strip=True)

def clean_markdown_for_chunking(text):
    """Clean markdown content using the data_preprocess.py approach"""
    # Step 1: Standardize known section headers
    
    # Replace "Table of Contents" with proper markdown header
    text = re.sub(r"(?m)^Table of Contents", r"## Table of Contents", text)
    
    # Normalize PART headers like "PART I"
    text = re.sub(r"(?m)^PART\s+([IVXLC]+)", r"## PART \1 —", text)
    
    # Normalize "Item 1. Business" to "### Item 1: Business"
    text = re.sub(r"(?m)^Item\s+(\d+)[.:]?\s+(.*)", r"### Item \1: \2", text)
    
    # Optional: upgrade detected ALL CAPS or underlined headers
    text = re.sub(r"(?m)^([A-Z][A-Z\s]+)\n[-=]{3,}", r"#### \1", text)
    
    # Step 2: Reduce triple or more newlines to double
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    return text

async def handle_html(url, row_metadata=None):
    """Handle HTML URLs using simple crawl4ai logic from cr.py"""
    # Generate dynamic filename
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace('.', '_')
    path = parsed_url.path.strip('/').replace('/', '_') or 'home'
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    filename = f"{domain}_{path}"
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
        )
        
        # Add metadata frontmatter if available
        content = result.markdown
        if row_metadata is not None:
            metadata = create_metadata_frontmatter(row_metadata)
            content = add_frontmatter_to_content(content, metadata)
        
        # Save the markdown to a file with dynamic name
        cleaned_output_file = os.path.join(CLEANED_DIR, f"{filename}.md")
        with open(cleaned_output_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"✅ HTML content saved to: {cleaned_output_file}")
        print(f"📄 Content length: {len(content)} characters")
        
        return cleaned_output_file

def handle_txt(url, row_metadata=None):
    """Handle .txt URLs (SEC filings) using exp.py logic"""
    # Generate filename based on URL
    parsed_url = urlparse(url)
    path = parsed_url.path.strip('/').replace('/', '_')
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    filename = f"sec_{path}"
    
    async def process_txt():
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    # Focus on text content
                    only_text=True,
                    
                    # Exclude problematic tags
                    excluded_tags=["script", "style", "noscript"],
                    
                    # Use crawl4ai's custom markdown generator
                    markdown_generator=DefaultMarkdownGenerator(
                        content_filter=PruningContentFilter(threshold=0.3)
                    ),
                    
                    # Content processing options
                    word_count_threshold=10,
                    
                    # Parser configuration
                    parser_type="lxml",
                    
                    # Remove forms
                    remove_forms=True,
                    
                    # Verbose logging
                    verbose=True
                )
            )
            
            # Get the main content from crawl4ai
            main_content = result.markdown.fit_markdown
            
            # Extract clean text using the data_preprocess.py approach
            clean_text = extract_clean_text_from_html(main_content)
            
            # Clean the markdown content
            cleaned_content = clean_markdown_for_chunking(clean_text)
            
            # Add metadata frontmatter if available
            if row_metadata is not None:
                metadata = create_metadata_frontmatter(row_metadata)
                cleaned_content = add_frontmatter_to_content(cleaned_content, metadata)
            
            # Save the cleaned content
            cleaned_output_file = os.path.join(CLEANED_DIR, f"{filename}.md")
            with open(cleaned_output_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            print(f"✅ Clean content saved to: {cleaned_output_file}")
            print(f"📄 Content length: {len(cleaned_content)} characters")
            
            return cleaned_output_file
    
    # Run the async function
    return asyncio.run(process_txt())

def download_and_clean(row):
    # Check for different file types based on available columns
    txt_url = row.get("linkToTxt")
    html_url = row.get("linkToHtml") or row.get("linkToFilingDetails")
    
    # Determine which URL to use based on what's available
    if txt_url and txt_url.startswith("http"):
        url = txt_url
        file_type = "txt"
        print(f"📄 Using linkToTxt for {row.get('ticker', 'UNK')}")
    elif html_url and html_url.startswith("http"):
        url = html_url
        file_type = "html"
        print(f"🌐 Using linkToHtml/linkToFilingDetails for {row.get('ticker', 'UNK')}")
    else:
        # Fallback to original method
        url = row.get("documentFormatFiles.documentUrl") or row.get("documentUrl")
        file_type = "unknown"
        print(f"❓ Using fallback URL for {row.get('ticker', 'UNK')}")
    
    if not url or not url.startswith("http"):
        failed.append((row.get("ticker", "UNK"), "No valid URL"))
        return

    try:
        # Determine file type and handle accordingly
        if file_type == "txt" or url.endswith('.txt'):
            # Handle SEC .txt files
            cleaned_file = handle_txt(url, row)
            print(f"✅ Processed SEC filing: {cleaned_file}")
        elif file_type == "html" or url.endswith('.html') or url.endswith('.htm'):
            # Handle HTML files
            cleaned_file = asyncio.run(handle_html(url, row))
            print(f"✅ Processed HTML file: {cleaned_file}")
        else:
            # Fallback to original method for other file types
            res = requests.get(url, timeout=20)
            res.raise_for_status()

            # Clean HTML
            soup = BeautifulSoup(res.text, "lxml")
            text = soup.get_text(separator="\n")
            
            # Add metadata frontmatter to fallback content
            metadata = create_metadata_frontmatter(row)
            content_with_metadata = add_frontmatter_to_content(text, metadata)
            
            # Save with metadata
            filename = get_filename_from_metadata(row)
            filepath = os.path.join(CLEANED_DIR, f"{filename}.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content_with_metadata)

            print(f"✅ Saved with metadata: {filename}.md")

    except Exception as e:
        failed.append((row.get("ticker", "UNK"), str(e)))
        print(f"❌ Failed: {row.get('ticker')} - {url[:60]}...")

if __name__ == "__main__":
    print(f"📥 Downloading {len(df)} filings...")

    for _, row in df.iterrows():
        download_and_clean(row)

    if failed:
        print("\n⚠️ Some downloads failed:")
        for f in failed:
            print("  -", f)
    else:
        print("🎉 All filings downloaded successfully!")
