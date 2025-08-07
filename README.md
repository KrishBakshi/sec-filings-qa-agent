# 📄 SEC Filings QA System

A semantic question-answering system that lets users query **SEC filings** (10-K, 8-K, DEF 14A, etc.) across multiple companies using **LangChain**, **ChromaDB**, and **Gemini 2.0 Flash**.  
Built for deep financial research with attribution, conversational memory, and full-stack pipeline integration.

---

## 🔍 Key Features

- 🧠 Natural language QA over SEC filings using Gemini Flash
- 📚 Semantic chunking + embedding with `sentence-transformers`
- 🗂 Filing metadata captured and cited (ticker, section, date)
- 🧩 Memory of last question for conversational follow-ups
- ⚡ Fast retrieval from `ChromaDB` (vector store)
- 🖥️ Streamlit UI for interactive querying

---

## 📁 Project Structure

| File / Script                  | Description |
|-------------------------------|-------------|
| `get_metadata_from_api.py`    | Fetch filings metadata using `sec-api` |
| `csv_data_collect_preprocess.py` | Clean and flatten raw metadata |
| `add_metadata_frontmatter.py` | Add YAML metadata to `.md` sections |
| `chuncking_and_embedding.py`  | Split + embed markdown into ChromaDB |
| `retrive_from_db.py`          | Test vector retrieval (no LLM) |
| `llm.py`                      | QA pipeline using LangChain + Gemini |
| `app.py`                      | Streamlit interface for user queries |
| `metadata.csv`                | Exported filing metadata |
| `.env.example`                | Template for environment variables |

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/KrishBakshi/sec-filings-qa-agent.git
cd sec-filings-qa
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up API Keys

Rename the `.env.example` file and insert your Google API key:

```bash
mv .env.example .env
```

```env
GOOGLE_API_KEY=your_google_api_key_here
```

---

## 🧪 How to Run

### ➤ Step 1: Get Metadata

```bash
python get_metadata_from_api.py
```

### ➤ Step 2: Process the Data

```bash
python csv_data_collect_preprocess.py
```

### ➤ Step 3: Chunk + Embed into Vector DB

```bash
python chuncking_and_embedding.py
```

### ➤ Step 4: Test Retrieval (Optional)

```bash
python retrive_from_db.py
```

### ➤ Step 5: Launch QA App

```bash
streamlit run app.py
```

---

## 💡 Sample Questions

- "What are Apple’s risk factors in the latest 10-K?"
- "Compare R&D spending of Tesla and Microsoft."
- "How does JPMorgan describe climate-related risks?"
- "What are the executive compensation changes for UNH?"

---

## ✅ Answer Quality Strategy

| Metric              | How It's Handled |
|---------------------|------------------|
| **Accuracy**         | Filtered top-k Chroma retrieval with clean chunking |
| **Multi-part queries** | Prompt instructs Gemini to decompose questions |
| **Attribution**      | Filing metadata passed in context |
| **Uncertainty**      | Gemini instructed to say “not found” if no context |

---

## 🚧 Known Limitations

- No advanced UI filters (ticker/date/etc.) — yet  
- Accuracy depends on clean chunking and markdown structuring

---

## 📎 Tech Stack

- [LangChain](https://www.langchain.com/)
- [ChromaDB](https://www.trychroma.com/)
- [Gemini 2.0 Flash](https://ai.google.dev/)
- [sentence-transformers](https://www.sbert.net/)
- [Streamlit](https://streamlit.io/)
- [crawl4ai](https://github.com/unclecode/crawl4ai)

---

## 📄 License

MIT License © 2025 [Your Name]

---

## 👋 Contact  
Visit: [https://github.com/KrishBakshi] 
