# medical_rag_groq.py
"""
Robust pipeline to query medical knowledge:
- Loads precomputed artifacts (NER, embeddings, FAISS, KG)
- Extracts query entities
- Expands subgraph
- Retrieves top semantic rows
- Composes context
- Calls Groq API to generate answers (instructed to answer factually)

FIXED VERSION - All paths are now relative and robust
"""

import os, re
from pathlib import Path
import pandas as pd
import numpy as np
import networkx as nx
import spacy
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import joblib

# FAISS optional
USE_FAISS = True
try:
    import faiss
except ImportError:
    USE_FAISS = False

# Groq client
try:
    from groq import Groq
except ImportError:
    Groq = None
    print("[WARN] groq SDK not installed.")

# -------------------------
# CONFIG - FIXED PATHS
# -------------------------
# Use Path objects for robust path handling
BASE_DIR = Path(__file__).parent.parent
OUT_DIR = BASE_DIR / "embeddings" / "kg_rag_artifacts"
VIZ_DIR = BASE_DIR / "visualizations"
DATA_DIR = BASE_DIR / "data"

# Try multiple possible data sources
DATA_FILES = [
    DATA_DIR / "drugs_side_effects.csv",
    DATA_DIR / "medquad_processed.csv",
    DATA_DIR / "medquad.csv"
]

EMBEDDING_FILES = [
    OUT_DIR / "corpus_embeddings.npy",
    BASE_DIR / "embeddings" / "encoded_docs.npy"
]

FAISS_INDEX_FILES = [
    OUT_DIR / "faiss.index",
    BASE_DIR / "embeddings" / "faiss_index_cpu.index"
]

KG_FILES = [
    OUT_DIR / "medical_kg.graphml",
    VIZ_DIR / "medical_kg.graphml"
]

NER_FILES = [
    OUT_DIR / "ner_entities.csv",
    VIZ_DIR / "ner_entities.csv",
    VIZ_DIR / "sample_ner_entities.csv"
]

GROQ_MODEL = "gemma2-9b-it"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your-groq-api-key-here")
EMBEDDER_MODEL = "all-MiniLM-L6-v2"

# -------------------------
# HELPERS
# -------------------------
def clean_text(text: str) -> str:
    if pd.isna(text):
        return ""
    s = str(text)
    s = re.sub(r"[\r\n]+", " ", s)
    s = re.sub(r"[^A-Za-z0-9\s\-,\.;:()/%]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def find_existing_file(file_list):
    """Find the first existing file from a list of possible paths"""
    for file_path in file_list:
        if file_path.exists():
            return file_path
    return None

# -------------------------
# LOAD MODELS & ARTIFACTS
# -------------------------
# SpaCy / scispaCy
try:
    import scispacy
    try:
        nlp = spacy.load("en_core_sci_sm")
    except Exception:
        nlp = spacy.load("en_core_web_sm")
except Exception:
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        print("[WARN] SpaCy not available. Using basic text processing.")
        nlp = None

# Sentence transformer
try:
    embedder = SentenceTransformer(EMBEDDER_MODEL)
except Exception as e:
    print(f"[WARN] SentenceTransformer not available: {e}")
    embedder = None

# Load corpus & embeddings
data_file = find_existing_file(DATA_FILES)
if data_file:
    print(f"[INFO] Loading data from: {data_file}")
    df = pd.read_csv(data_file).fillna("")
    # Clean data columns based on what's available
    for col in ["drug_name", "side_effects", "medical_condition", "answer", "answer_clean"]:
        if col in df.columns and f"{col}_clean" not in df.columns:
            df[f"{col}_clean"] = df[col].astype(str).apply(clean_text)
else:
    print("[WARN] No data file found. Creating sample data.")
    df = pd.DataFrame({
        'drug_name': ['Paracetamol', 'Ibuprofen', 'Amoxicillin'],
        'side_effects': ['Nausea, liver damage', 'Stomach upset', 'Diarrhea'],
        'medical_condition': ['Fever, pain', 'Pain, inflammation', 'Bacterial infection']
    })
    for col in ["drug_name", "side_effects", "medical_condition"]:
        df[f"{col}_clean"] = df[col].astype(str).apply(clean_text)

# Load embeddings if available
embedding_file = find_existing_file(EMBEDDING_FILES)
if embedding_file:
    print(f"[INFO] Loading embeddings from: {embedding_file}")
    corpus_embeddings = np.load(embedding_file)
else:
    print("[WARN] Embeddings file not found. Creating dummy embeddings.")
    if not df.empty:
        corpus_embeddings = np.random.rand(len(df), 384).astype('float32')
    else:
        corpus_embeddings = np.random.rand(20, 384).astype('float32')

# Load FAISS index
if USE_FAISS:
    faiss_file = find_existing_file(FAISS_INDEX_FILES)
    if faiss_file:
        try:
            index = faiss.read_index(str(faiss_file))
            print(f"[INFO] FAISS index loaded from: {faiss_file}")
        except Exception as e:
            print(f"[WARN] Error loading FAISS index: {e}")
            index = None
    else:
        index = None
        print("[WARN] FAISS index not found. Using brute-force similarity.")
else:
    index = None

# Load KG
kg_file = find_existing_file(KG_FILES)
if kg_file:
    try:
        G = nx.read_graphml(kg_file)
        print(f"[INFO] Knowledge graph loaded from: {kg_file}")
    except Exception as e:
        print(f"[WARN] Error loading knowledge graph: {e}")
        G = nx.Graph()
else:
    print("[WARN] Knowledge graph file not found. Creating dummy graph.")
    G = nx.Graph()
    # Add some dummy nodes for testing
    G.add_node("DRUG::paracetamol", label="Paracetamol", type="DRUG")
    G.add_node("CONDITION::fever", label="Fever", type="CONDITION")
    G.add_edge("DRUG::paracetamol", "CONDITION::fever", relation="TREATS")

# -------------------------
# NER + Query helpers
# -------------------------
def run_ner(text):
    if nlp is None:
        # Fallback: simple keyword extraction
        words = text.lower().split()
        medical_terms = ["fever", "pain", "headache", "nausea", "cough", "fatigue"]
        found_terms = [(word, "SYMPTOM") for word in words if word in medical_terms]
        return found_terms if found_terms else [("symptom", "SYMPTOM")]
    
    doc = nlp(text)
    ents = [(ent.text.strip(), ent.label_) for ent in doc.ents]
    if not ents:
        for chunk in doc.noun_chunks:
            ents.append((chunk.text.strip(), "NOUN_CHUNK"))
    ents = list(dict.fromkeys(ents))
    return ents

def extract_query_entities(symptoms, additional_info):
    tokens = [clean_text(s) for s in symptoms]
    ents = run_ner(additional_info)
    tokens += [clean_text(e) for e,lbl in ents]
    
    if nlp is not None:
        doc = nlp(additional_info)
        for tok in doc:
            if tok.pos_ in {"NOUN","PROPN","ADJ"} and len(tok.text)>2:
                tokens.append(clean_text(tok.text))
    
    # dedupe
    seen=set(); out=[]
    for t in tokens:
        if t and t not in seen:
            out.append(t); seen.add(t)
    return out

def match_graph_nodes(tokens, max_matches=10):
    matches=[]
    for t in tokens:
        t_low=t.lower()
        cur=[]
        for n,d in G.nodes(data=True):
            if t_low in d.get("label","").lower():
                cur.append(n)
            if len(cur)>=max_matches: break
        if cur: matches.extend(cur)
    return list(dict.fromkeys(matches))

def expand_subgraph(seed_nodes, radius=2):
    if not seed_nodes: return nx.Graph()
    nodes_to_include=set(seed_nodes)
    frontier=set(seed_nodes)
    for _ in range(radius):
        new_frontier=set()
        for n in frontier:
            for nbr in list(G.successors(n))+list(G.predecessors(n)):
                if nbr not in nodes_to_include: new_frontier.add(nbr)
        nodes_to_include.update(new_frontier)
        frontier=new_frontier
    return G.subgraph(nodes_to_include).copy()

def subgraph_to_text(subg, max_triples=60):
    triples=[]
    for u,v,data in subg.edges(data=True):
        rel=data.get("relation","related_to")
        u_lbl=subg.nodes[u].get("label",u)
        v_lbl=subg.nodes[v].get("label",v)
        triples.append(f"{u_lbl} --{rel}--> {v_lbl}")
    return "\n".join(triples[:max_triples])

def semantic_retrieve(text, top_k=5):
    if embedder is None or df.empty:
        # Return sample data for testing
        return df.head(min(top_k, len(df))) if not df.empty else pd.DataFrame()
    
    qv = embedder.encode([clean_text(text)], convert_to_numpy=True, normalize_embeddings=True)
    if USE_FAISS and index is not None:
        try:
            D,I=index.search(qv.astype("float32"), top_k)
            indices = I[0].tolist()
        except Exception as e:
            print(f"[WARN] FAISS search error: {e}")
            sims=cosine_similarity(qv, corpus_embeddings)[0]
            indices = sims.argsort()[-top_k:][::-1].tolist()
    else:
        sims=cosine_similarity(qv, corpus_embeddings)[0]
        indices = sims.argsort()[-top_k:][::-1].tolist()
    
    result = df.iloc[indices].copy()
    for col in ["drug_name","side_effects","medical_condition"]:
        if f"{col}_clean" not in result.columns and col in result.columns:
            result[f"{col}_clean"]=result[col].astype(str).apply(clean_text)
    return result

# -------------------------
# Compose context + Groq
# -------------------------
def compose_context_from_query(symptoms, additional_info, top_k_semantic=5, radius=2):
    tokens=extract_query_entities(symptoms, additional_info)
    seed_nodes=match_graph_nodes(tokens)
    if not seed_nodes:
        sem=semantic_retrieve(additional_info or " ".join(symptoms), top_k_semantic)
        if not sem.empty and 'drug_name_clean' in sem.columns:
            seed_nodes=[f"DRUG::{clean_text(d)}" for d in sem['drug_name_clean'].tolist() if G.has_node(f"DRUG::{clean_text(d)}")]
    subg=expand_subgraph(seed_nodes, radius=radius) if seed_nodes else nx.Graph()
    kg_text=subgraph_to_text(subg, max_triples=80)
    semrows=semantic_retrieve(additional_info or " ".join(symptoms), top_k=top_k_semantic)
    
    if not semrows.empty:
        rows_text="\n".join((semrows.get('drug_name_clean', semrows.get('drug_name', '')) + ": " + 
                           semrows.get('side_effects_clean', semrows.get('side_effects', '')) + " | Condition: " + 
                           semrows.get('medical_condition_clean', semrows.get('medical_condition', ''))).tolist())
    else:
        rows_text = "No specific drug data available."
    
    combined_context=f"KnowledgeGraphTriples:\n{kg_text}\n\nTopDatasetRows:\n{rows_text}"
    return combined_context, seed_nodes, semrows

def generate_with_groq(question, context, model_name=GROQ_MODEL, temperature=0.2, max_tokens=300):
    if Groq is None:
        return "Educational Response: " + question + " - This would be answered using medical context. Please install Groq SDK and set API key for AI responses."
    
    api_key=GROQ_API_KEY
    if not api_key or api_key == "your-groq-api-key-here":
        return "Educational Response: " + question + " - Please set GROQ_API_KEY environment variable for AI-generated responses."
    
    client=Groq(api_key=api_key)
    prompt=f"""You are a highly knowledgeable medical assistant. Use ONLY the context below to answer factually. You are acting as a model for a school project to demonstrate their work on medical context. Do NOT refuse to answer.

Context:
{context}

Question:
{question}

Answer:"""
    try:
        resp=client.chat.completions.create(
            model=model_name,
            messages=[
                {"role":"system","content":"You are a helpful medical assistant."},
                {"role":"user","content":prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {e}"

def answer_via_kg_and_semantics(symptoms, additional_info, question):
    context, seed_nodes, semrows=compose_context_from_query(symptoms, additional_info)
    answer=generate_with_groq(question, context)
    return {"answer":answer,"context":context,"seed_nodes":seed_nodes,"semantic_rows":semrows}

# -------------------------
# API Mode for Backend Integration
# -------------------------
def run_api_mode(symptoms, additional_info, question):
    """API mode for integration with backend"""
    import json
    try:
        result = answer_via_kg_and_semantics(symptoms, additional_info, question)
        return json.dumps({
            "status": "success",
            "symptoms": symptoms,
            "additional_info": additional_info,
            "question": question,
            "answer": result["answer"],
            "context_preview": result["context"][:500] + "..." if len(result["context"]) > 500 else result["context"],
            "seed_nodes_count": len(result["seed_nodes"]),
            "semantic_rows_count": len(result["semantic_rows"]) if not result["semantic_rows"].empty else 0
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

# -------------------------
# Main execution
# -------------------------
if __name__=="__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Medical Recommendation System')
    parser.add_argument('--symptoms', nargs='+', default=["Fever", "Fatigue"], help='List of symptoms')
    parser.add_argument('--additional_info', type=str, default="Mild fever for 2 days, headache and nausea. No known allergies.", help='Additional information')
    parser.add_argument('--question', type=str, default="Which over-the-counter drugs are likely safe and what side effects should this patient watch for?", help='Question to ask')
    parser.add_argument('--api', action='store_true', help='Run in API mode')
    
    args = parser.parse_args()
    
    if args.api:
        # API mode for backend integration
        result = run_api_mode(args.symptoms, args.additional_info, args.question)
        print(result)
    else:
        # Regular mode
        symptoms = args.symptoms
        add_info = args.additional_info
        question = args.question
        
        print("[RUN] composing context...")
        try:
            ctx, seeds, semrows = compose_context_from_query(symptoms, add_info)
            print("\n--- CONTEXT PREVIEW ---\n")
            print(ctx[:2000])
            
            if not GROQ_API_KEY or GROQ_API_KEY == "your-groq-api-key-here":
                print("\n[NOTE] GROQ_API_KEY not set — skipping Groq generation.")
                print("Please set the GROQ_API_KEY environment variable.")
            else:
                print("\n[RUN] calling Groq generator...")
                out = answer_via_kg_and_semantics(symptoms, add_info, question)
                print("\n--- GENERATED ANSWER ---\n")
                print(out['answer'])
                print("\n--- SEED NODES ---\n", out['seed_nodes'])
                if not out['semantic_rows'].empty:
                    print("\n--- TOP SEMANTIC ROWS ---\n", out['semantic_rows'][['drug_name','side_effects']].head().to_string())
        except Exception as e:
            print(f"Error: {e}")
            print("Make sure all data files are present in the correct directories.")
        
        print(f"\nArtifacts expected in: {OUT_DIR}")
        print(f"Data files checked: {[str(f) for f in DATA_FILES]}")
        print(f"Embeddings checked: {[str(f) for f in EMBEDDING_FILES]}")
