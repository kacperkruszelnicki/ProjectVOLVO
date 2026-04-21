import requests
import json
import pickle
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)

# CONFIG
API_KEY = "hf_..."
API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"
INPUT_FILE = "prepared_data.pkl"

# Loading prepared data
try:
    with open(INPUT_FILE, "rb") as f:
        store = pickle.load(f)
        documents = store["documents"]
        vectorizer = store["vectorizer"]
        doc_vectors = store["doc_vectors"]
except FileNotFoundError:
    print(f"ERROR: File: {INPUT_FILE} not found!")

def log_error(question, reason, sources=None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    src_text = f" | SOURCES: {', '.join(sources)}" if sources else " | SOURCES: None"
    log_entry = f"[{timestamp}] QUESTION: {question} | REASON: {reason}{src_text}\n"
    with open("rag_errors.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)

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

def query_llm(context, question, profile):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    system_prompt = f"You are a strict RAG assistant. RULES: Answer ONLY based on context and following user Profile: {profile} and make sure the documents are not conflicting"
    user_prompt = f"CONTEXT:\n{context}\n\nQUESTION: {question}"
    
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()}
        ],
        "max_tokens": 400,
        "temperature": 0.1
    }
    r = requests.post(API_URL, headers=headers, json=payload, timeout=30)

    return r.json()["choices"][0]["message"]["content"] if r.status_code == 200 else "API ERROR"

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

def ask(question, profile="business"):
    docs = search(question)
    if not docs:
        # Logging the lack of matching documents
        log_error(question, "No matching documents found")
        return {"answer": "I do not know based on provided context.", "sources": []}

    context = "\n".join([f"[{d['source']}]\n{d['content']}" for d in docs])
    
    conflict_result = detect_conflict_structured(docs)
    if conflict_result != "NO_CONFLICT":
        source_names = [d["source"] for d in docs]
        # Logging conflicting information
        log_error(question, f"Conflict: {conflict_result}", sources=source_names)
        return {
            "answer": f"Detected conflicting information: {conflict_result}",
            "sources": source_names
        }
    answer = query_llm(context, question, profile)
    return {"answer": answer, "sources": [d["source"] for d in docs]}

# --- API interface ---
@app.route("/ask", methods=["POST"])
def api_ask():
    data = request.json
    return jsonify(ask(data.get("question", ""), data.get("profile", "business")))

def run_cli():
    print("RAG Chatbot - type 'exit' to finish\n")
    while True:
        question = input("Question: ")
        if question.lower() == "exit": break
        profile = input("Profil (business/engineer/architect): ")
        result = ask(question, profile)
        print(f"\nAnswer: {result['answer']}\nSources: {result['sources']}\n{'-'*50}")

if __name__ == "__main__":
    MODE = "cli" # Change mode to run api
    if MODE == "cli": run_cli()
    else: app.run(port=5000)
