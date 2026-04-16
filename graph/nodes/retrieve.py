# /graph/nodes/retrieve.py

from typing import Any, Dict
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
# state.py bir üst klasörde olduğu için '..' kullanıyoruz ve doğrudan GraphState sınıfını alıyoruz
from ..state import GraphState

# Retriever'ı diskteki veritabanından kendimiz oluşturuyoruz
print("--- Vektör Veritabanına Bağlanılıyor ---")
vectorstore = Chroma(
    collection_name="rag-chroma",
    persist_directory="./.chroma",
    embedding_function=OpenAIEmbeddings(),
)
retriever = vectorstore.as_retriever()
print("--- Retriever Başarıyla Oluşturuldu ---")


# --- DÜZELTİLEN KISIM BURASI ---
# Type hint'ten "state." ön eki kaldırıldı.
def retrieve(state: GraphState) -> Dict[str, Any]:
    """
    Verilen soruya göre vektör veritabanından ilgili belgeleri alır.
    """
    print("---RETRIEVE DÜĞÜMÜ ÇALIŞIYOR---")
    question = state["question"]

    documents = retriever.invoke(question)

    return {"documents": documents, "question": question}