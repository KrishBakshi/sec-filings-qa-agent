import asyncio
import re
from datetime import datetime
from urllib.parse import urlparse
from crawl4ai import *

async def main():
    url = "https://www.sec.gov/Archives/edgar/data/1821159/000155837025010333/evgo-20250630x10q.htm"
    
    # Generate dynamic filename
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace('.', '_')
    path = parsed_url.path.strip('/').replace('/', '_') or 'home'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    filename = f"{domain}_{path}_{timestamp}.md"
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
        )
        
        # Save the markdown to a file with dynamic name
        with open(filename, "w", encoding="utf-8") as f:
            f.write(result.markdown)
        
        print(f"Markdown content saved to {filename}")

if __name__ == "__main__":
    asyncio.run(main())