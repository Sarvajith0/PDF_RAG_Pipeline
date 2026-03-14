from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from data import retriever

model = OllamaLLM(model="deepseek-r1:14b")

template = """
You are an expert in answering questions about data from PDF tables.

Here are some relevant table excerpts:
{reviews}

Here is the question to answer: {question}

Rules:
- Answer only from the table data provided above
- Be specific and include exact numbers or values
- If the answer is not in the data, say "This information is not available in the provided tables"
- Always mention the table NAME and NUMBER the answer came from
- If multiple tables have the same answer, mention all of them
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

while True:
    print("\n\n-------------------------------")
    question = input("Ask your question (q to quit): ")
    print("\n\n")
    if question == "q":
        break

    # reviews = retriever.invoke(question)
    
    reviews = retriever.invoke(question)
    print("DEBUG - Retrieved chunks:")
    for doc in reviews:
        print(doc.page_content[:200])
        print("---")
    result = chain.invoke({"reviews": reviews, "question": question})
    print(result)