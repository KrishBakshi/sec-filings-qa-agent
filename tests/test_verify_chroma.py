import chromadb
import os

# Test the saved database
CHROMA_DB_DIR = "chroma_db_test"

print(f"🔍 Testing ChromaDB at: {os.path.abspath(CHROMA_DB_DIR)}")

# Connect to the saved database
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# Get the collection
collection = chroma_client.get_collection(name="sec_filings_test")

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
        
    print(f"\n✅ Data is successfully stored and retrievable from ChromaDB!")
    print(f"📁 Database location: {os.path.abspath(CHROMA_DB_DIR)}")
    
else:
    print("⚠️ Collection exists but is empty") 