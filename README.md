A local RAG pipeline that extracts tables from PDFs, 
embeds them using Ollama, and answers natural language 
questions using DeepSeek-R1 and ChromaDB.

The Complete Flow in One Diagram:
```mermaid
flowchart TD
    A[PDF File] --> B[extractor.py
pdfplumber]
    B --> C[knowledge_base.json]
    C --> D[data.py
qwen3-embedding]
    D --> E[(ChromaD
Vector Store)]
    F[User Question] --> G[Retriever
top 3 tables]
    E --> G
    F --> H[Prompt Builder]
    G --> H
    H --> I[DeepSeek-R1
via Ollama]
    I --> J[Strip think tags]
    J --> K[Final Answer]
```
LLMs used via Ollama:
  deepseek-r1:14b Q4_K_M for answer generation
  qwen3-embedding:4b for embedding
Vector DB used: 
  ChromaDB

Why RAG Is Better Than Just Asking the LLM:
Without RAG:
Question → LLM → Answer (from training data, may hallucinate)
With RAG:
Question → Retrieve exact data → LLM reads data → Accurate answer


Can modify the LLMs used for answer generation in query1.py(5) and embedding in data.py(13)
