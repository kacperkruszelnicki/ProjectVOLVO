import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from docx import Document
from pypdf import PdfReader
import json
from flask_cors import CORS
from flask import Flask, request, jsonify

app = Flask(__name__)
CORS(app)

# CONFIG
API_KEY = "hf_..."
API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"

def load_docx(path):
    try:
        doc = Document(path)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Loading error {path}: {e}")
        return ""

def load_pdf(path):
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text
    except Exception as e:
        print(f"Loading error {path}: {e}")
        return ""

# List of docx documents in local directory (optional)
docx_files = [
    "dokument1.docx",
    "dokument2.docx",
    "dokument3.docx",
    "dokument4.docx",
    "dokument5.docx",
    "dokument6.docx"
]
# List of pdf documents in local directory (optional)
pdf_files = [
    "dokument1.pdf",
    "dokument2.pdf"
    ]

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

# loads text content from docx files
def chunk_text(text, size=300, overlap=80):
    chunks = []
    start = 0

    while start < len(text):
        chunk = text[start:start + size]
        chunks.append(chunk)
        start += size - overlap

    return chunks


for i, file in enumerate(docx_files):
    content = load_docx(file)

    chunks = chunk_text(content)

    for j, chunk in enumerate(chunks):
        documents.append({
            "content": chunk,
            "source": f"{file}_chunk{j}"
        })

for file in pdf_files:
    content = load_pdf(file)
    chunks = chunk_text(content)
    for j, chunk in enumerate(chunks):
        documents.append({
            "content": chunk,
            "source": f"{file}_chunk{j}"
        })

# Finds top-k relevant documents based on cosine similarity.
def search(query, k=4, threshold=0.15):
    query_vec = vectorizer.transform([query])
    similarities = cosine_similarity(query_vec, doc_vectors)[0]

    top_indices = similarities.argsort()[::-1][:k]

    results = []
    for idx in top_indices:
        if similarities[idx] >= threshold:
            results.append(documents[idx])

    return results

# LLM (API)
def query_llm(context, question, profile):

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = f"""
You are a strict RAG assistant.

RULES:
- Answer ONLY based on provided context
- If information is missing say: "I don't know based on provided data"
- If documents contain conflicting information, clearly state:
  "The available data is conflicting"
- Do NOT try to resolve conflicts using external knowledge
- Do NOT guess
- Target your explanation style to the user profile:
{profile}
"""

    user_prompt = f"""
CONTEXT:
{context}

TASK:
1. Answer the question using ONLY the context
2. Check if context contains contradictions
3. If contradictions exist: say it clearly

QUESTION:
{question}
"""

    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()}
        ],
        "max_tokens": 400,
        "temperature": 0.1
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    if response.status_code != 200:
        return f"API ERROR {response.status_code}: {response.text}"

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Parsing error: {str(response.json())}"

def build_index(docs):
    texts = [d["content"] for d in docs]
    vectorizer = TfidfVectorizer()
    doc_vectors = vectorizer.fit_transform(texts)
    return vectorizer, doc_vectors

vectorizer, doc_vectors = build_index(documents)

# Extracting number of stages of a process described in a document
def extract_pipeline_info(context):

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_ID,
        "messages": [
            {
                "role": "system",
                "content": "Extract structured information."
            },
            {
                "role": "user",
                "content": f"""
                Extract information about process stages.

                Return ONLY JSON:

                {{
                    "num_stages": number or null,
                    "stages": [list of stages],
                    "notes": short description
                }}

                TEXT:
                {context}
                """
            }
        ],
        "temperature": 0.0
    }
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=30)

        if r.status_code != 200:
            return f"API ERROR: {r.text}"

        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {str(e)}"

def detect_conflict_structured(docs):

    extracted = []

    for d in docs:
        info = extract_pipeline_info(d["content"])
        try:
            extracted.append(json.loads(info))
        except:
            continue

    stage_counts = set()

    for e in extracted:
        if e["num_stages"]:
            stage_counts.add(e["num_stages"])

    if len(stage_counts) > 1:
        return "CONFLICT: different number of stages"

    return "NO_CONFLICT"

def detect_conflicts_with_llm(context):

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_ID,
        "messages": [
            {
                "role": "system",
                "content": "You have to detect only strong contradictions in provided documents"
            },
            {
                "role": "user",
                "content": f"""
                DOCUMENTS:
                {context}

                TASK:
                Only detect contradiction if:
                - statements cannot both be true

                DO NOT treat as contradiction:
                - additional explanation
                - more detailed description
                - extended information

                Example:
                3 stages vs detailed description - NOT conflict
                3 stages vs 2 stages - conflict
                """
            }
        ],
        "max_tokens": 300,
        "temperature": 0.1
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        return f"API ERROR {response.status_code}: {response.text}"

    try:
        result = response.json()["choices"][0]["message"]["content"]
        return result.strip()
    except:
        return "ERROR_PARSING"

def ask(question, profile="business"):

    docs = search(question)

    if not docs:
        return {
            "answer": "I do not know based on provided context.",
            "sources": []
        }

    context = "\n".join([f"[{d['source']}]\n{d['content']}" for d in docs])
    
    #conflict_result = detect_conflicts_with_llm(context)
    conflict_result = detect_conflict_structured(docs)
    if conflict_result != "NO_CONFLICT" and conflict_result != "NOT_SURE":
        return {
            "answer": f"Detected conflicting information in the documents:\n\n{conflict_result}",
            "sources": [d["source"] for d in docs]
        }

    if conflict_result == "NOT_SURE":
            print(f"Detected potentially conflicting information: {conflict_result}")
            print(f"sources: ", [d["source"] for d in docs])
    if conflict_result == "NO_CONFLICT":
        answer = query_llm(context, question, profile)
    

        return {
            "answer": answer,
            "sources": [d["source"] for d in docs]
        }


# CLI
def run_cli():
    print("RAG Chatbot - type 'exit' to finish\n")

    while True:
        question = input("Question: ")

        if question.lower() == "exit":
            break

        profile = input("Profil (business/engineer/architect): ")

        result = ask(question, profile)

        print("\nAnswer:")
        print(result["answer"])

        if result["sources"]:
            print("\nSources:")
            for s in result["sources"]:
                print("-", s)

        print("\n" + "-" * 50)


# API FLASK
@app.route("/ask", methods=["POST"])
def api_ask():
    data = request.json
    question = data.get("question", "")
    profile = data.get("profile", "business")

    result = ask(question, profile)
    return jsonify(result)


# START
if __name__ == "__main__":
    MODE = "cli"   # cli = run in terminal, api = run in flask

    if MODE == "cli":
        run_cli()

    elif MODE == "api":
        app.run(port=5000)
