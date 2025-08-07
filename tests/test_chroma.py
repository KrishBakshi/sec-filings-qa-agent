import chromadb
import os

# Setup Chroma client
CHROMA_DB_DIR = "chroma_db"

# Check if ChromaDB directory exists
if not os.path.exists(CHROMA_DB_DIR):
    print("❌ ChromaDB directory not found!")
    print(f"Expected path: {os.path.abspath(CHROMA_DB_DIR)}")
    exit(1)

print(f"✅ ChromaDB directory found: {CHROMA_DB_DIR}")

# Setup Chroma client
chroma_client = chromadb.Client(chromadb.config.Settings(
    persist_directory=CHROMA_DB_DIR
))

# Check if collection exists
try:
    collection = chroma_client.get_collection(name="sec_filings")
    print("✅ Collection 'sec_filings' found!")
    
    # Get collection info
    count = collection.count()
    print(f"📊 Total documents in collection: {count}")
    
    if count > 0:
        print("\n📄 Sample documents:")
        # Get first few documents
        results = collection.get(limit=3)
        
        for i, (doc_id, doc, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            print(f"\n--- Document {i+1} ---")
            print(f"ID: {doc_id}")
            print(f"Content preview: {doc[:200]}...")
            print(f"Metadata: {metadata}")
            
        print(f"\n✅ Data is successfully stored in ChromaDB!")
        print(f"📁 Database location: {os.path.abspath(CHROMA_DB_DIR)}")
        
    else:
        print("⚠️ Collection exists but is empty")
        
except Exception as e:
    print(f"❌ Error accessing collection: {e}")
    print("\nAvailable collections:")
    try:
        collections = chroma_client.list_collections()
        for col in collections:
            print(f"  - {col.name}")
    except Exception as e2:
        print(f"  Error listing collections: {e2}") 