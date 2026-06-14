import os
import pickle
import datetime
from docx import Document
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import faiss
import numpy as np
import re

from image_extract import extract_and_describe_images
RAW_DIR = "data/raw"
# CONFIG
DOCX_FILES = [
    os.path.join(RAW_DIR, plik) 
    for plik in os.listdir(RAW_DIR) 
    if os.path.isfile(os.path.join(RAW_DIR, plik)) and plik.lower().endswith('.docx')
]
PDF_FILES = [
    os.path.join(RAW_DIR, plik) 
    for plik in os.listdir(RAW_DIR) 
    if os.path.isfile(os.path.join(RAW_DIR, plik)) and plik.lower().endswith('.pdf')
]

OUTPUT_FILE = "data/processed/prepared_data_faiss.pkl"
# Model for creating embeddings
#MODEL_NAME = 'all-MiniLM-L6-v2'
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
#LOCAL_MODEL_PATH = "models/all-MiniLM-L6-v2"
LOCAL_MODEL_PATH = "models/paraphrase-multilingual-MiniLM-L12-v2"

def load_or_download_model():
    if os.path.exists(LOCAL_MODEL_PATH):
        print(f"Loading model from local folder: {LOCAL_MODEL_PATH}")
        return SentenceTransformer(LOCAL_MODEL_PATH)
    else:
        print(f"Downloading model: {MODEL_NAME}")
        model = SentenceTransformer(MODEL_NAME)
        
        print(f"Saving model locally to: {LOCAL_MODEL_PATH}")
        os.makedirs(LOCAL_MODEL_PATH, exist_ok=True)
        model.save(LOCAL_MODEL_PATH)
        
        return model

# Simple predefined documents
documents = [
    {
        "content": """Pipeline danych to proces przetwarzania danych składający się z kilku etapów.
        Pierwszym etapem jest ingest danych, czyli pobieranie danych z różnych źródeł takich jak API,
        bazy danych lub pliki. Następnie dane przechodzą transformację, gdzie są czyszczone,
        agregowane oraz przekształcane do odpowiedniego formatu. Ostatnim etapem jest ładowanie danych
        do docelowego systemu, np. hurtowni danych lub data lake.""",
        "source": "doc1",
        "last_modified": "2023-01-01 10:00:00",
        "tags": ["architecture", "data-engineering", "pipeline"],
        "status": "effective",
        "implementation_status": "completed"
    },
    {
        "content": """Architektura medallion jest podejściem do organizacji danych w warstwach.
        Warstwa bronze zawiera dane surowe w niezmienionej formie. Warstwa silver zawiera dane
        przetworzone i oczyszczone. Warstwa gold zawiera dane gotowe do analizy biznesowej.
        Podejście to pozwala na lepszą kontrolę jakości danych oraz ich transformacji.""",
        "source": "doc2",
        "last_modified": "2023-05-15 12:00:00",
        "tags": ["medallion", "lakehouse", "organization"],
        "status": "effective",
        "implementation_status": "completed"
    },
    {
        "content": """Data lake to centralne repozytorium danych, które przechowuje dane w ich
        natywnej, surowej formie. Umożliwia przechowywanie zarówno danych strukturalnych,
        jak i niestrukturalnych. Data lake jest często wykorzystywany w systemach big data
        oraz w analizie danych na dużą skalę. W przeciwieństwie do hurtowni danych,
        nie wymaga wcześniejszego schematu danych.""",
        "source": "doc3",
        "last_modified": "2023-08-20 09:30:00",
        "tags": ["data-lake", "storage", "big-data"],
        "status": "effective",
        "implementation_status": "completed"
    }
]

def get_file_metadata(path):
    """Gets last modification date of a file."""
    try:
        mtime = os.path.getmtime(path)
        return datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_docx(path):
    try:
        doc = Document(path)
        text = "\n".join([p.text for p in doc.paragraphs])
        
        # Szybki dostęp do core_properties
        props = doc.core_properties
        
        # 1. Odczyt właściwości wbudowanych (zamiast custom_properties)
        # Używamy 'or', aby przypisać domyślną wartość, jeśli pole jest puste (None)
        status = props.content_status or "draft"
        impl_status = props.category or "n/a"
        
        # 2. Odczyt wbudowanej, prawdziwej daty modyfikacji dokumentu
        dt = props.modified
        last_mod = dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None
        
        return text, status, impl_status, last_mod
        
    except Exception as e:
        print(f"❌ Błąd podczas ładowania pliku {path}: {e}")
        return "", "draft", "n/a", None
    except Exception as e:
        print(f"DOCX loading error {path}: {e}")
        return "", "draft", "n/a", None

def load_pdf(path):
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content: text += content + "\n"
            
        # 1. Odczyt metadanych ze struktury PDF
        meta = reader.metadata or {}
        status = meta.get("/status", "draft")
        impl_status = meta.get("/implementatio_status", "n/a")
        
        # 2. Parsowanie daty modyfikacji zapisanej w PDF
        last_mod = None
        pdf_date = meta.get("/ModDate", "")
        if pdf_date and pdf_date.startswith("D:"):
            try:
                dt = datetime.datetime.strptime(pdf_date[2:14], "%Y%m%d%H%M")
                last_mod = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
                
        return text, status, impl_status, last_mod
    except Exception as e:
        print(f"PDF loading error {path}: {e}")
        return "", "draft", "n/a", None

def chunk_text(text, size=500, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        step = max(1, size - overlap)
        start += step
    return chunks

def split_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def semantic_chunk_text(
    text,
    semantic_model,
    similarity_threshold=0.40,
    max_chunk_sentences=8,
    min_chunk_sentences=3,
    min_chunk_chars = 80
):

    sentences = split_sentences(text)

    if len(sentences) <= 1:
        return [text]

    sentence_embeddings = semantic_model.encode(sentences)

    chunks = []
    current_chunk = [sentences[0]]
    current_embeddings = [sentence_embeddings[0]]

    for i in range(1, len(sentences)):

        # embedding of new sentence
        new_embedding = sentence_embeddings[i]

        # mean embedding of current chunk
        chunk_embedding = np.mean(current_embeddings, axis=0)

        # similarity chunk vs new sentence
        sim = cosine_similarity(
            [chunk_embedding],
            [new_embedding]
        )[0][0]

        # decision
        if (
            sim >= similarity_threshold
            or len(current_chunk) < min_chunk_sentences
        ) and len(current_chunk) < max_chunk_sentences:

            current_chunk.append(sentences[i])
            current_embeddings.append(new_embedding)

        else:
            chunks.append(" ".join(current_chunk))

            current_chunk = [sentences[i]]
            current_embeddings = [new_embedding]

    # last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    chunks = [c for c in chunks if len(c) >= min_chunk_chars]
    return chunks

def run_preparation():
    print(f"Loading embedding model: {MODEL_NAME}...")
    model = load_or_download_model()

    all_docs = []

    print("\n--- TEST ŚCIEŻEK ---")
    for test_file in DOCX_FILES:
        pelna_sciezka = os.path.abspath(test_file)
        czy_istnieje = os.path.exists(pelna_sciezka)
        print(f"Szukam pliku: {pelna_sciezka}")
        print(f"Czy istnieje? {'✅ TAK' if czy_istnieje else '❌ NIE'}")
    print("--------------------\n")

    # Processing external files
    for file_list, loader in [(DOCX_FILES, load_docx), (PDF_FILES, load_pdf)]:
        for file in file_list:
            if not os.path.exists(file):
                continue
            
            # POPRAWKA 1: Rozpakowujemy 4 wartości bezpośrednio wyciągnięte z pliku
            content, file_status, file_impl_status, file_last_mod = loader(file)
            
            # POPRAWKA 2: Jeśli plik nie miał wewnętrznej daty, używamy rezerwowej z systemu operacyjnego
            if not file_last_mod:
                file_last_mod = get_file_metadata(file)
                
            if content:
                # chunks = chunk_text(content)
                chunks = semantic_chunk_text(content, model)
                for j, chunk in enumerate(chunks):
                    all_docs.append({
                        "content": chunk,
                        "source": file,
                        "last_modified": file_last_mod,
                        "tags": ["file_import", file.split('.')[-1]],
                        "status": file_status,             # Używamy wartości z pliku
                        "type": "text",
                        "implementation_status": file_impl_status  # Używamy wartości z pliku
                    })

            # Dla ekstrakcji obrazów przekazujemy również aktualne dane z pliku
            image_chunks = extract_and_describe_images(file, file_last_mod, file_status)
            if image_chunks:
                all_docs.extend(image_chunks)

    print(f"Generating embeddings for {len(all_docs)} chunks...")
    texts = [d["content"] for d in all_docs]
    embeddings = model.encode(texts)
    
    # FAISS init
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))

    # Writing DB
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    data_to_save = {
        "documents": all_docs,
        "faiss_index": faiss.serialize_index(index),
        "model_name": LOCAL_MODEL_PATH
    }
    
    with open(OUTPUT_FILE, "wb") as f:
        pickle.dump(data_to_save, f)
    
    print(f"Success! Data saved to '{OUTPUT_FILE}'.")

if __name__ == "__main__":
    run_preparation()
