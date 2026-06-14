import json
import pickle
import datetime
import os
from docx import Document
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer

# List of documents in local directory
RAW_DIR = "data/raw"
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
OUTPUT_FILE = "prepared_data.pkl"

# DOCUMENTS
documents = [
    {
        "content": """Pipeline danych to proces przetwarzania danych składający się z kilku etapów.
        Pierwszym etapem jest ingest danych, czyli pobieranie danych z różnych źródeł takich jak API,
        bazy danych lub pliki. Następnie dane przechodzą transformację, gdzie są czyszczone,
        agregowane oraz przekształcane do odpowiedniego formatu. Ostatnim etapem jest ładowanie danych
        do docelowego systemu, np. hurtowni danych lub data lake.""",
        "source": "doc1"
    },
    {
        "content": """Architektura medallion jest podejściem do organizacji danych w warstwach.
        Warstwa bronze zawiera dane surowe w niezmienionej formie. Warstwa silver zawiera dane
        przetworzone i oczyszczone. Warstwa gold zawiera dane gotowe do analizy biznesowej.
        Podejście to pozwala na lepszą kontrolę jakości danych oraz ich transformacji.""",
        "source": "doc2"
    },
    {
        "content": """Data lake to centralne repozytorium danych, które przechowuje dane w ich
        natywnej, surowej formie. Umożliwia przechowywanie zarówno danych strukturalnych,
        jak i niestrukturalnych. Data lake jest często wykorzystywany w systemach big data
        oraz w analizie danych na dużą skalę. W przeciwieństwie do hurtowni danych,
        nie wymaga wcześniejszego schematu danych.""",
        "source": "doc3"
    }
]

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
        impl_status = meta.get("/implementationStatus", "n/a")
        
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

def chunk_text(text, size=300, overlap=80):
    if overlap >= size:
        raise ValueError("Overlap must be smaller than size to avoid infinite loops!")
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks

def run_preparation():
    print("Preparing data...")
    
    # 1. Processing DOCX
    for file in DOCX_FILES:
        # Rozpakowujemy 4 wartości zwracane przez funkcję
        content, status, impl_status, last_mod = load_docx(file)
        
        # Jeśli plik nie był pusty, przetwarzamy tekst
        if content:
            for j, chunk in enumerate(chunk_text(content)):
                documents.append({
                    "content": chunk, 
                    "source": f"{file}_chunk{j}",
                    "status": status,
                    "implementation_status": impl_status,
                    "last_modified": last_mod if last_mod else "1970-01-01 00:00:00"
                })

    # 2. Processing PDF
    for file in PDF_FILES:
        # Rozpakowujemy 4 wartości zwracane przez funkcję
        content, status, impl_status, last_mod = load_pdf(file)
        
        # Jeśli plik nie był pusty, przetwarzamy tekst
        if content:
            for j, chunk in enumerate(chunk_text(content)):
                documents.append({
                    "content": chunk, 
                    "source": f"{file}_chunk{j}",
                    "status": status,
                    "implementation_status": impl_status,
                    "last_modified": last_mod if last_mod else "1970-01-01 00:00:00"
                })

    # Building index TF-IDF
    print(f"Indexing {len(documents)} chunks...")
    vectorizer = TfidfVectorizer()
    
    # Teraz d["content"] na pewno jest czystym stringiem tekstowym
    texts = [d["content"] for d in documents]
    doc_vectors = vectorizer.fit_transform(texts)

    # Saving to the file
    data_to_save = {
        "documents": documents,
        "vectorizer": vectorizer,
        "doc_vectors": doc_vectors
    }
    
    with open(OUTPUT_FILE, "wb") as f:
        pickle.dump(data_to_save, f)
    
    print(f"Success! Data saved in {OUTPUT_FILE}.")

if __name__ == "__main__":
    run_preparation()
