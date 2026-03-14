from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "knowledge_base.json")

with open("knowledge_base.json", "r", encoding="utf-8") as f:
    knowledge_base = json.load(f)

embeddings = OllamaEmbeddings(model="qwen3-embedding:4b")

db_location = "./chroma_langchain_db"
add_documents = not os.path.exists(db_location)

if add_documents:
    documents = []
    ids = []

    for table in knowledge_base["tables"]:
        document = Document(
            page_content=table["text_summary"],        # what gets embedded and searched
            metadata={
                "table_id": table["id"],
                "table_name": table["name"],
                "page": table["page"],
                "type": "table"
            },
            id=table["id"]
        )
        ids.append(table["id"])
        documents.append(document)

vector_store = Chroma(
    collection_name="pdf_tables",
    persist_directory=db_location,
    embedding_function=embeddings
)

if add_documents:
    vector_store.add_documents(documents=documents, ids=ids)
    print(f"Embedded {len(documents)} tables into ChromaDB")
else:
    print("ChromaDB already exists, skipping embedding step")
#relevant tables
retriever = vector_store.as_retriever(
    search_kwargs={"k": 3}
)