import os
import glob
import yaml
import chromadb
from uuid import uuid4
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import time

# Setup paths
MARKDOWN_DIR = "cleaned_filings"
CHROMA_DB_DIR = "chroma_db"

# Load model
print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Setup Chroma client
print(f"Saving DB to: {os.path.abspath(CHROMA_DB_DIR)}")
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
collection = chroma_client.get_or_create_collection(name="sec_filings")

# Text splitter config
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ".", " "]
)

# Helper to parse frontmatter
def parse_markdown_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if content.startswith("---"):
        parts = content.split("---", 2)
        metadata = yaml.safe_load(parts[1])
        body = parts[2].strip()
        return metadata, body
    else:
        return {}, content.strip()

# Process all markdown files with batching
filepaths = glob.glob(os.path.join(MARKDOWN_DIR, "*.md"))
print(f"Found {len(filepaths)} markdown files to split + ingest")

# Batch processing variables
all_chunks = []
all_metadatas = []
all_ids = []
batch_size = 100  # Process chunks in batches

start_time = time.time()

for path in filepaths:
    print(f"Processing: {os.path.basename(path)}")
    metadata, body = parse_markdown_file(path)
    if not body or len(body) < 100:
        continue

    chunks = text_splitter.split_text(body)
    print(f"{os.path.basename(path)} → {len(chunks)} chunks")

    # Prepare batch data
    for i, chunk in enumerate(chunks):
        uid = str(uuid4())
        
        # Extend metadata with chunk index
        metadata_chunked = {
            **metadata,
            "chunk_index": i,
            "source_doc": os.path.basename(path)
        }

        all_chunks.append(chunk)
        all_metadatas.append(metadata_chunked)
        all_ids.append(uid)

        # Process in batches
        if len(all_chunks) >= batch_size:
            print(f"Generating embeddings for batch of {len(all_chunks)} chunks...")
            batch_start = time.time()
            
            # Generate embeddings for the entire batch at once
            embeddings = model.encode(all_chunks)
            
            # Add to ChromaDB in batch
            collection.add(
                documents=all_chunks,
                metadatas=all_metadatas,
                ids=all_ids,
                embeddings=embeddings.tolist()
            )
            
            batch_time = time.time() - batch_start
            print(f"Batch processed in {batch_time:.2f}s ({len(all_chunks)} chunks)")
            
            # Reset batch
            all_chunks = []
            all_metadatas = []
            all_ids = []

# Process remaining chunks
if all_chunks:
    print(f"Processing final batch of {len(all_chunks)} chunks...")
    batch_start = time.time()
    
    # Generate embeddings for the final batch
    embeddings = model.encode(all_chunks)
    
    # Add to ChromaDB in batch
    collection.add(
        documents=all_chunks,
        metadatas=all_metadatas,
        ids=all_ids,
        embeddings=embeddings.tolist()
    )
    
    batch_time = time.time() - batch_start
    print(f"Final batch processed in {batch_time:.2f}s ({len(all_chunks)} chunks)")

# ChromaDB persists automatically in newer versions
print("ChromaDB data is automatically persisted to disk")
total_time = time.time() - start_time
print(f"All documents chunked, embedded and stored in Chroma!")
print(f"Total processing time: {total_time:.2f}s")
