import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# --- HATA ÇÖZÜMÜ İÇİN DEĞİŞTİRİLEN KISIM BAŞLANGICI ---

# PDF kaynakları
pdf_files = [
    "data/1.pdf",
    "data/2.pdf",
    "data/3.pdf",
]

print("Belge yükleme işlemi başlıyor...")
docs = []
try:
    for pdf in pdf_files:
        if not os.path.exists(pdf):
            print(f"HATA: Belirtilen dosya bulunamadı: {pdf}")
            continue  # Bu dosyayı atla ve devam et
        print(f"{pdf} yükleniyor...")
        loader = PyPDFLoader(pdf)
        docs.extend(loader.load())
    if not docs:
        print("HATA: Hiçbir belge yüklenemedi. Lütfen dosya yollarını kontrol edin.")
        exit(1)
    print("Tüm belgeler başarıyla yüklendi.")
except Exception as e:
    print(f"HATA: Belge yüklenirken bir sorun oluştu: {e}")
    exit(1)

# Chunklama
print("Belgeler parçalara ayrılıyor (chunking)...")
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=500,
    chunk_overlap=80
)
doc_splits = text_splitter.split_documents(docs)
print(f"Chunking işlemi tamamlandı. Toplam {len(doc_splits)} parça oluşturuldu.")

# Embedding modelini ve veritabanı yolunu tanımla
embedding_function = OpenAIEmbeddings()
persist_directory = "./.chroma"
collection_name = "rag-chroma"

# Önce vectorstore nesnesini oluştur (veya var olana bağlan)
print("Vektör veritabanına bağlanılıyor veya oluşturuluyor...")
vectorstore = Chroma(
    collection_name=collection_name,
    embedding_function=embedding_function,
    persist_directory=persist_directory,
)

# Belgeleri gruplar halinde eklemek için batch boyutu belirle
batch_size = 100
total_batches = (len(doc_splits) + batch_size - 1) // batch_size  # Toplam batch sayısını hesapla

print(f"{len(doc_splits)} belge {total_batches} grup halinde veritabanına eklenecek.")

for i in range(0, len(doc_splits), batch_size):
    # Mevcut batch'i al
    batch = doc_splits[i:i + batch_size]
    batch_number = (i // batch_size) + 1
    print(f"Grup {batch_number}/{total_batches} işleniyor...")

    # Mevcut batch'i vectorstore'a ekle
    vectorstore.add_documents(batch)

print("Tüm gruplar başarıyla işlendi.")
print("Vektör veritabanı kalıcı olarak kaydedildi.")
print("Ingestion tamamlandı! PDF'ler vektör veritabanına başarıyla kaydedildi.")

# --- HATA ÇÖZÜMÜ İÇİN DEĞİŞTİRİLEN KISIM SONU ---