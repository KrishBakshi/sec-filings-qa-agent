import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Load .env with GOOGLE_API_KEY
load_dotenv()

# Config
CHROMA_DB_DIR = "chroma_db"
COLLECTION_NAME = "sec_filings"

# Initialize embedding model (same as used earlier)
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Connect to Chroma DB
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embedding_model,
    persist_directory=CHROMA_DB_DIR
)

# Retriever with optional metadata filters
retriever = vectorstore.as_retriever(search_kwargs={
    "k": 5  # top-k chunks
})

# Initialize Gemini 2.0 Flash via LangChain
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.2,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Prompt template
prompt = PromptTemplate.from_template("""
You are a financial research analyst AI assistant.
Answer the following question using only the context below. 
Cite the source (ticker, filing_type, section, filing_date) where relevant.

Question: {question}

Context:
{context}

Helpful Answer:
""")

# Chain: retrieve → prompt → Gemini
def format_docs(docs):
    return "\n\n".join(
        f"[{d.metadata.get('ticker')}, {d.metadata.get('filing_type')}, {d.metadata.get('section')}, {d.metadata.get('filing_date')}]:\n{d.page_content}"
        for d in docs
    )

chain = (
    RunnableLambda(lambda q: retriever.get_relevant_documents(q))
    | RunnableLambda(lambda docs: {
        "context": format_docs(docs),
        "question": docs[0].metadata.get("original_query", "") if docs else ""
    })
    | prompt
    | llm
)

# ⌨️ Ask a question
if __name__ == "__main__":
    query = input("Ask a financial research question: ")
    result = chain.invoke(query)
    print("\nGemini Answer:\n")
    print(result.content)
