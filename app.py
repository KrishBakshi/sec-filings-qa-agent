import os
import streamlit as st
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

# Load API key
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

# Config
CHROMA_DB_DIR = "chroma_db"
COLLECTION_NAME = "sec_filings"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Init embedding + Chroma
embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embedding_model,
    persist_directory=CHROMA_DB_DIR
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# Gemini Flash via LangChain
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.2,
    google_api_key=GOOGLE_API_KEY
)

# Prompt
prompt = PromptTemplate.from_template("""
Role:
You are a financial research analyst AI assistant.
Answer the following question using only the context below. 

Format:
- Keep the answer concise, simple, understandable and to the point.
- Ensure that the answer is uniform in style and struture, transform the answer if needed . 
- Answer with relevant citations.
- Cite the source (ticker, filing_type, filing_date[Year-Month]) where relevant.

constraints:
- If the question is not relavent to the context, please donnot answer, return "Sorry, I don't have the information to answer that question."
- If the question is not clear, please ask for clarification.
- Donot provide your own opinion on the question, only answer the question based on the context.

Chat History:
{history}

Question: {question}

Context:
{context}

Answer:
""")

# Chat session history init
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Combine: retrieve → prompt → Gemini
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


# Streamlit UI
st.set_page_config(page_title="SEC Filings QA", layout="wide")
st.title("📄 SEC Filings QA System (LangChain + Gemini)")
st.markdown("Ask questions about 10-K, 8-K, DEF 14A filings across companies.")

query = st.text_input("🔍 Ask a financial question", placeholder="E.g. What are Tesla's recent risk factors?")
run_button = st.button("🔎 Run Query")

if run_button and query:
    # Retrieve new context
    docs = retriever.get_relevant_documents(query)
    context = format_docs(docs)

    # Build history as string
    history_text = ""
    for turn in st.session_state.chat_history:
        history_text += f"Q: {turn['question']}\nA: {turn['answer']}\n\n"

    # Send to LLM
    chain_input = {
        "question": query,
        "context": context,
        "history": history_text.strip()
    }
    with st.spinner("Thinking..."):
        answer = llm.invoke(prompt.format(**chain_input)).content

    # Store in session
    st.session_state.chat_history.append({
        "question": query,
        "answer": answer,
        "context": context
    })

# st.subheader("📂 Retrieved Documents")
# docs = retriever.get_relevant_documents(query)
# for i, d in enumerate(docs):
#     meta = d.metadata
#     st.markdown(f"**{i+1}. [{meta.get('ticker')} - {meta.get('filing_type')} - {meta.get('section')} - {meta.get('filing_date')}]**")
#     st.code(d.page_content[:800] + "...", language="markdown")

# Display full conversation
if st.session_state.chat_history:
    st.subheader("🧠 Conversation History")
    for i, turn in enumerate(st.session_state.chat_history):
        st.markdown(f"**Q{i+1}:** {turn['question']}")
        st.markdown(f"**A{i+1}:** {turn['answer']}")
        with st.expander("🔍 Context used"):
            # st.code(turn['context'][:2000] + "..." if len(turn['context']) > 2000 else turn['context'], language="markdown")
            st.subheader("📂 Retrieved Documents")
            docs = retriever.get_relevant_documents(query)
            for i, d in enumerate(docs):
                meta = d.metadata
                st.markdown(f"**{i+1}. [{meta.get('ticker')} - {meta.get('filing_type')} - {meta.get('section')} - {meta.get('filing_date')}]**")
                st.code(d.page_content[:800] + "...", language="markdown")