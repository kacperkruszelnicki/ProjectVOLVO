import os
from dotenv import load_dotenv
import requests
import json
import pickle
import datetime
import faiss
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer

app = Flask(__name__)
CORS(app)

# CONFIG
load_dotenv()
API_KEY = os.getenv("HF_API_KEY")
API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"

INPUT_FILE = "data/processed/prepared_data_faiss.pkl"

# Loading data and model
try:
    with open(INPUT_FILE, "rb") as f:
        store = pickle.load(f)
        documents = store["documents"]
        index = faiss.deserialize_index(store["faiss_index"])
        model = SentenceTransformer(store["model_name"])
    print("FAISS DB loaded successfully.")
except Exception as e:
    print(f"CANNOT LOAD DB: {e}")

STATUS_WEIGHTS = {
    "effective": 1.0,
    "reviewing": 0.8,
    "draft": 0.5,
    "archived": 0.2,
    "obsolete": 0.0
}

IMPLEMENTATION_WEIGHTS = {
    "completed": 1.0,
    "on_going": 0.8,
    "poc": 0.6,
    "plan": 0.4,
    "n/a": 0.5
}

def log_event(question, reason, sources=None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if sources:
        src_text = " | SOURCES: " + ", ".join(sources)
    else:
        src_text = " | SOURCES: None"
    
    log_entry = f"[{timestamp}] QUESTION: {question} | REASON: {reason}{src_text}\n"
    
    try:
        with open("logs/rag_logs.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print("Logging error:", e)

def search_faiss(query, k=8, threshold=30.0):
    query_vector = model.encode([query]).astype('float32')
    distances, indices = index.search(query_vector, k)
    
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        # FAISS IndexFlatL2 (smaller distance = greater similarity)
        if idx != -1 and dist <= threshold:
            doc = documents[idx].copy()
            doc['score'] = float(dist)
            results.append(doc)
    return results

def safe_json_loads(text):
    """Cleans LLM response and attempts to parse JSON."""
    if not text:
        return None

    try:
        clean = text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        print("JSON parsing error:", e)
        print("RAW OUTPUT:", text)
        return None

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

def detect_and_resolve_conflicts_smart(docs):
    extracted = []
    rejected_info = []

    # extraction
    for d in docs:
        raw = extract_pipeline_info(d["content"])
        parsed = safe_json_loads(raw)

        if parsed and parsed.get("num_stages") is not None:
            extracted.append({
                "doc": d,
                "num_stages": parsed["num_stages"]
            })

    # grouping
    groups = {}
    for e in extracted:
        groups.setdefault(e["num_stages"], []).append(e["doc"])

    if not groups:
        return docs, "NO_DATA", []

    if len(groups) == 1:
        return docs, "NO_CONFLICT", []

    # scoring
    def compute_score(doc):
        # freshness (timestamp)
        try:
            timestamp = datetime.datetime.strptime(
                doc.get("last_modified", "1970-01-01 00:00:00"),
                "%Y-%m-%d %H:%M:%S"
            ).timestamp()
        except:
            timestamp = 0
        
        freshness_score = timestamp / 2000000000
        
        # semantic similarity
        faiss_score = 1 / (1 + doc.get("score", 1.0))
        
        # status
        status_score = STATUS_WEIGHTS.get(
            doc.get("status", "draft"),
            0.5
        )

        # Added part
        implementation_score = IMPLEMENTATION_WEIGHTS.get(
            doc.get("implementation_status", "n/a"),
            0.5
        )
        
        final_score = (
            freshness_score * 0.35 +
            faiss_score * 0.35 +
            status_score * 0.2 +
            implementation_score * 0.1
        )
        #final_score = (
         #   freshness_score * 0.4 +
          #  faiss_score * 0.4 +
           # status_score * 0.2
        #)
        
        return final_score

    group_scores = {}

    for stage_count, group_docs in groups.items():
        scores = [compute_score(d) for d in group_docs]
        group_scores[stage_count] = max(scores)

    # choosing best group
    best_stage = max(group_scores, key=group_scores.get)
    best_docs = groups[best_stage]

    # information about rejected documents
    for stage_count, group_docs in groups.items():
        if stage_count == best_stage:
            continue

        for d in group_docs:
            rejected_info.append({
                "rejected_doc": d["source"],
                "rejected_stages": stage_count,
                "conflicted_with_stages": best_stage,
                "conflicted_with_docs": [bd["source"] for bd in best_docs]
            })

    status = f"RESOLVED_CONFLICT (kept stage_count={best_stage})"

    return best_docs, status, rejected_info

def ask(question, profile="business"):
    initial_docs = search_faiss(question)
    # removing obsolete documents
    initial_docs = [d for d in initial_docs if d.get("status") != "obsolete"]
    if not initial_docs:
        log_event(question, "No matching documents found")
        return {"answer": "No appropriate data found.", "sources": []}

    # Detecting and resolving conflicts
    final_docs, status, rejected = detect_and_resolve_conflicts_smart(initial_docs)
    print(f"Status of chosen documents: {status}")

    if rejected:
        print(f"Rejected documents: {rejected}")
        log_event(
            question,
            f"Conflict resolved: {status}",
            sources=[r["rejected_doc"] for r in rejected]
        )

    context = "\n".join([f"[Source: {d['source']} | Date: {d['last_modified']}]\n{d['content']}" for d in final_docs])
    
    system_prompts = {
        "business": "You are a business analyst. Focus on business value, costs, and goals. Keep answers clear and concise.",
        "engineer": "You are a data engineer. Focus on technical implementation, ETL, and architecture.",
        "architect": "You are a system architect. Focus on scalability, integration, and long-term data strategy."
    }

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    prompt = f"User: {profile}. Answer the question using only provided context. Status: {status}.\n\nCONTEXT:\n{context}\n\nQUESTION: {question}"
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": system_prompts.get(profile, system_prompts["business"])},
            {"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        answer = r.json()["choices"][0]["message"]["content"]
        return {
            "answer": answer,
            "sources": [f"{d['source']} | {d['status']} | ({d['last_modified']})" for d in final_docs],
            "status": status,
            "rejected": rejected
        }
    except Exception as e:
        log_event(question, f"API ERROR: {str(e)}")
        return {"answer": f"API ERROR: {str(e)}", "sources": []}

@app.route("/ask", methods=["POST"])
def api_ask():
    data = request.json
    return jsonify(ask(data.get("question", ""), data.get("profile", "business")))

if __name__ == "__main__":
    # Start in CLI by default
    while True:
        q = input("\nQuestion (or 'exit'): ")
        if q.lower() == 'exit': break
        prof = input("Profil (business/engineer/architect): ").lower() or "business"
        res = ask(q, prof)
        print(f"\nANSWER: {res['answer']}")
        print(f"SOURCES: {res['sources']}")
