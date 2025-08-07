import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Config
CHROMA_DB_DIR = "chroma_db"
COLLECTION_NAME = "sec_filings"

# Load embedding model (must match chunking step)
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Load Chroma vector store
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embedding_model,
    persist_directory=CHROMA_DB_DIR
)

# Basic retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# Sample test query
query = input("Enter your test query: ")

# Run retrieval
results = retriever.get_relevant_documents(query)

print(f"\nRetrieved {len(results)} chunks for: \"{query}\"\n")

for i, doc in enumerate(results, 1):
    meta = doc.metadata
    preview = doc.page_content[:300].strip().replace("\n", " ")
    print(f"Result {i}:")
    print(f"   - Ticker       : {meta.get('ticker')}")
    print(f"   - Filing Type  : {meta.get('filing_type')}")
    print(f"   - Section      : {meta.get('section')}")
    print(f"   - Filing Date  : {meta.get('filing_date')}")
    print(f"   - Source Doc   : {meta.get('source_doc')}")
    print(f"   - Chunk Index  : {meta.get('chunk_index')}")
    print(f"   - Preview      : {preview}...\n")
