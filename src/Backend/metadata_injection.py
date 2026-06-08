import os
import datetime
from docx import Document
from pypdf import PdfReader, PdfWriter
import random

# CONFIG
RAW_DIR = "data/raw"

# 1. Automatyczne pobranie wszystkich plików z folderu (z poprzedniego kroku)
PDF_FILES = [os.path.join(RAW_DIR, plik) for plik in os.listdir(RAW_DIR) if os.path.isfile(os.path.join(RAW_DIR, plik))]
DOCX_FILES = []  # Pusta lista, skoro masz same PDFy

# 2. Definiujemy dostępne pule statusów (zgodne z wagami w Twoim Flasku)
MOZLIWE_STATUSY = ["effective", "reviewing", "draft", "archived", "obsolete"]
MOZLIWE_IMPLEMENTACJE = ["completed", "on_going", "poc", "plan", "n/a"]

# 3. Dynamiczne i losowe generowanie słowników dla wszystkich wykrytych plików
DOCUMENT_STATUS = {
    plik: random.choice(MOZLIWE_STATUSY) for plik in PDF_FILES
}

IMPLEMENTATION_STATUS = {
    plik: random.choice(MOZLIWE_IMPLEMENTACJE) for plik in PDF_FILES
}

# --- PODGLĄD (Możesz usunąć, służy do weryfikacji w konsoli) ---
print("\n🎲 WYLOSOWANE STATUSY DOKUMENTÓW:")
for k, v in DOCUMENT_STATUS.items():
    print(f"  ▪️ {k} -> {v}")

print("\n🎲 WYLOSOWANE STATUSY WDROŻENIA:")
for k, v in IMPLEMENTATION_STATUS.items():
    print(f"  ▪️ {k} -> {v}")
# --- FUNKCJE DLA DOCX ---

def zapisz_i_weryfikuj_docx(path, status, impl_status):
    if not os.path.exists(path):
        print(f"❌ Plik nie istnieje: {path}")
        return

    print(f"\n📝 Przetwarzanie DOCX: {path}")
    
    # 1. ZAPIS
    doc = Document(path)
    custom_props = doc.custom_properties
    
    # Dodawanie lub aktualizacja tagu Status
    try:
        custom_props['status'] = status
    except KeyError:
        custom_props.add_property('status', status)
        
    # Dodawanie lub aktualizacja tagu ImplementationStatus
    try:
        custom_props['implementation_status'] = impl_status
    except KeyError:
        custom_props.add_property('implementation_status', impl_status)
    
    # Wymuszenie aktualizacji wbudowanej daty modyfikacji na "teraz"
    doc.core_properties.modified = datetime.datetime.now()
    doc.save(path)
    print("  [OK] Metadane zostały zapisane.")

    # 2. ODCZYT (WERYFIKACJA)
    doc_check = Document(path)
    odczytany_status = doc_check.custom_properties.get('status', 'BRAK')
    odczytany_impl = doc_check.custom_properties.get('implementation_status', 'BRAK')
    odczytana_data = doc_check.core_properties.modified
    
    print("  🔍 Weryfikacja odczytu:")
    print(f"    ▪️ status:                 {odczytany_status}")
    print(f"    ▪️ implementation_status:   {odczytany_impl}")
    print(f"    ▪️ Last Modified (Word):   {odczytana_data}")


# --- FUNKCJE DLA PDF ---

def zapisz_i_weryfikuj_pdf(path, status, impl_status):
    if not os.path.exists(path):
        print(f"❌ Plik nie istnieje: {path}")
        return

    print(f"\n📝 Przetwarzanie PDF: {path}")
    
    # 1. ZAPIS (W PDF musimy przepisać plik przez PdfWriter)
    reader = PdfReader(path)
    writer = PdfWriter()
    
    # Kopiujemy strony
    for page in reader.pages:
        writer.add_page(page)
        
    # Kopiujemy dotychczasowe metadane (jeśli są) i dodajemy nasze
    nowe_metadane = {k: v for k, v in (reader.metadata or {}).items()}
    nowe_metadane["/status"] = status
    nowe_metadane["/mplementation_status"] = impl_status
    
    # Generujemy datę w formacie PDF (np. D:20260607140000Z)
    teraz_pdf = "D:" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "Z"
    nowe_metadane["/ModDate"] = teraz_pdf
    
    writer.add_metadata(nowe_metadane)
    
    # Zapisujemy pod tą samą ścieżką
    with open(path, "wb") as f:
        writer.write(f)
    print("  [OK] Metadane zostały zapisane.")

    # 2. ODCZYT (WERYFIKACJA)
    reader_check = PdfReader(path)
    meta = reader_check.metadata or {}
    
    print("  🔍 Weryfikacja odczytu:")
    print(f"    ▪️ status:                 {meta.get('/status', 'BRAK')}")
    print(f"    ▪️ implementation_status:   {meta.get('/implementation_status', 'BRAK')}")
    print(f"    ▪️ ModDate (PDF raw):      {meta.get('/ModDate', 'BRAK')}")


# --- GŁÓWNY PROCES ---

if __name__ == "__main__":
    print("=== ROZPOCZĘCIE INIEKCJI I WERYFIKACJI METADANYCH ===")

    
    # Przetwarzanie PDF-ów
    for file in PDF_FILES:
        status = DOCUMENT_STATUS.get(file, "draft")
        impl_status = IMPLEMENTATION_STATUS.get(file, "n/a")
        zapisz_i_weryfikuj_pdf(file, status, impl_status)
        
    print("\n=== PROCES ZAKOŃCZONY ===")