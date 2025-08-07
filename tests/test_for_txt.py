import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from bs4 import BeautifulSoup
import re
import os

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

async def extract_markdown():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.sec.gov/Archives/edgar/data/80661/000008066125000051/0000080661-25-000051.txt",
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
        
        # Create output directory
        os.makedirs("markdown_output", exist_ok=True)
        
        # Get the main content from crawl4ai
        main_content = result.markdown.fit_markdown
        
        # Extract clean text using the data_preprocess.py approach
        clean_text = extract_clean_text_from_html(main_content)
        
        # Clean the markdown content
        cleaned_content = clean_markdown_for_chunking(clean_text)
        
        # Save the cleaned content
        cleaned_output_file = "markdown_output/sec_document_clean.md"
        with open(cleaned_output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        # Also save the original main content for reference
        main_output_file = "markdown_output/sec_document_main.md"
        with open(main_output_file, 'w', encoding='utf-8') as f:
            f.write(main_content)
        
        print(f"Clean content saved to: {cleaned_output_file}")
        print(f"Main content saved to: {main_output_file}")
        print(f"Content length: {len(cleaned_content)} characters")

# Run the async function
asyncio.run(extract_markdown())
