import os
import pickle
import datetime
from docx import Document
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# CONFIG
DOCX_FILES = ["dokument1.docx", "dokument2.docx", "dokument3.docx", "dokument4.docx", "dokument5.docx", "dokument6.docx"]
PDF_FILES = ["dokument1.pdf", "dokument2.pdf"]
OUTPUT_FILE = "prepared_data_faiss.pkl"
# Model for creating embeddings
MODEL_NAME = 'all-MiniLM-L6-v2'
LOCAL_MODEL_PATH = "models/all-MiniLM-L6-v2"

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
        "tags": ["architecture", "data-engineering", "pipeline"]
    },
    {
        "content": """Architektura medallion jest podejściem do organizacji danych w warstwach.
        Warstwa bronze zawiera dane surowe w niezmienionej formie. Warstwa silver zawiera dane
        przetworzone i oczyszczone. Warstwa gold zawiera dane gotowe do analizy biznesowej.
        Podejście to pozwala na lepszą kontrolę jakości danych oraz ich transformacji.""",
        "source": "doc2",
        "last_modified": "2023-05-15 12:00:00",
        "tags": ["medallion", "lakehouse", "organization"]
    },
    {
        "content": """Data lake to centralne repozytorium danych, które przechowuje dane w ich
        natywnej, surowej formie. Umożliwia przechowywanie zarówno danych strukturalnych,
        jak i niestrukturalnych. Data lake jest często wykorzystywany w systemach big data
        oraz w analizie danych na dużą skalę. W przeciwieństwie do hurtowni danych,
        nie wymaga wcześniejszego schematu danych.""",
        "source": "doc3",
        "last_modified": "2023-08-20 09:30:00",
        "tags": ["data-lake", "storage", "big-data"]
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
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        print(f"DOCX loading error {path}: {e}")
        return ""

def load_pdf(path):
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content: text += content + "\n"
        return text
    except Exception as e:
        print(f"PDF loading error {path}: {e}")
        return ""

def chunk_text(text, size=500, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        step = max(1, size - overlap)
        start += step
    return chunks

def run_preparation():
    print(f"Loading embedding model: {MODEL_NAME}...")
    model = load_or_download_model()

    all_docs = documents.copy()

    # Processing external files
    for file_list, loader in [(DOCX_FILES, load_docx), (PDF_FILES, load_pdf)]:
        for file in file_list:
            if not os.path.exists(file):
                continue
            content = loader(file)
            last_mod = get_file_metadata(file)
            if content:
                chunks = chunk_text(content)
                for j, chunk in enumerate(chunks):
                    all_docs.append({
                        "content": chunk,
                        "source": file,
                        "last_modified": last_mod,
                        "tags": ["file_import", file.split('.')[-1]]
                    })

    print(f"Generating embeddings for {len(all_docs)} chunks...")
    texts = [d["content"] for d in all_docs]
    embeddings = model.encode(texts)
    
    # FAISS init
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))

    # Writing DB
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
