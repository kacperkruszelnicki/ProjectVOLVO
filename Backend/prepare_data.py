import json
import pickle
import datetime
from docx import Document
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer

# List of documents in local directory
DOCX_FILES = ["dokument1.docx", "dokument2.docx", "dokument3.docx", "dokument4.docx", "dokument5.docx", "dokument6.docx"]
PDF_FILES = ["dokument1.pdf", "dokument2.pdf"]
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
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        print(f"Loading error {path}: {e}")
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
        print(f"Loading error {path}: {e}")
        return ""

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
    
    # Processing DOCX
    for file in DOCX_FILES:
        content = load_docx(file)
        if content:
            for j, chunk in enumerate(chunk_text(content)):
                documents.append({"content": chunk, "source": f"{file}_chunk{j}"})

    # Processing PDF
    for file in PDF_FILES:
        content = load_pdf(file)
        if content:
            for j, chunk in enumerate(chunk_text(content)):
                documents.append({"content": chunk, "source": f"{file}_chunk{j}"})

    # Building index TF-IDF
    print(f"Indexing {len(documents)}")
    vectorizer = TfidfVectorizer()
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
