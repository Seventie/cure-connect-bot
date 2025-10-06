# med_qa_pipeline_groq_clean.py

import os
import numpy as np
import pandas as pd
import faiss
import torch
from transformers import DPRQuestionEncoder, DPRQuestionEncoderTokenizer
from groq import Groq

# -------------------------------
# 1. Load data and prebuilt embeddings
# -------------------------------
df = pd.read_csv("data/medquad_processed.csv") # preprocessed dataset
docs = df["answer_clean"].astype(str).tolist()
encoded_docs = np.load("embeddings/encoded_docs.npy")
encoded_docs = encoded_docs / np.linalg.norm(encoded_docs, axis=1, keepdims=True)
dimension = encoded_docs.shape[1]
index = faiss.IndexFlatIP(dimension)
index.add(encoded_docs)
print("[INFO] FAISS index built successfully (in-memory).")

# -------------------------------
# 2. Load DPR encoders
# -------------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
print("[INIT] Loading DPR encoders...")
question_encoder = DPRQuestionEncoder.from_pretrained(
    "facebook/dpr-question_encoder-single-nq-base"
).to(device)
question_tokenizer = DPRQuestionEncoderTokenizer.from_pretrained(
    "facebook/dpr-question_encoder-single-nq-base"
)
print("[INFO] DPR encoders loaded successfully.")

# -------------------------------
# 3. Setup Groq client
# -------------------------------
api_key = os.getenv("GROQ_API_KEY", "your-groq-api-key-here")
client = Groq(api_key=api_key)

# -------------------------------
# 4. Helper functions
# -------------------------------
def retrieve_context(question: str, top_k: int = 5):
    """Retrieve top-k relevant contexts using FAISS."""
    inputs = question_tokenizer(
        question, return_tensors="pt", truncation=True, max_length=512
    ).to(device)
    with torch.no_grad():
        q_emb = question_encoder(**inputs).pooler_output.cpu().numpy()
        q_emb = q_emb / np.linalg.norm(q_emb, axis=1, keepdims=True)
    scores, indices = index.search(q_emb, top_k)
    retrieved_texts = [docs[i] for i in indices[0]]
    return " ".join(retrieved_texts)

def generate_answer_groq(question: str, context: str) -> str:
    """Generate factual medical answer using Groq model."""
    prompt = f"""
You are a knowledgeable medical assistant designed for educational and informational purposes only.
Your task is to provide clear, factually accurate, and educational answers.

Follow these instructions carefully:
1. Use the provided context primarily to form your answer.
2. If the context does not fully answer the question, provide a brief, logical, and educational explanation using your general medical understanding.
3. Indicate which parts of the provided context were most relevant to your answer.
4. Do NOT give warnings like "I cannot provide medical advice" — instead, frame everything as educational information.

Context:
{context}

Question:
{question}

Answer (for educational purposes only):
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERROR calling Groq API] {e}"

# -------------------------------
# 5. Main QA function
# -------------------------------
def ask_question(question: str, top_k: int = 5):
    """Get context, retrieve top docs, and generate answer."""
    context = retrieve_context(question, top_k=top_k)
    answer = generate_answer_groq(question, context)
    return answer

# -------------------------------
# 6. Interactive Run & API Mode
# -------------------------------
def run_api_mode(question: str, top_k: int = 5):
    """API mode for integration with backend"""
    import json
    try:
        answer = ask_question(question, top_k)
        return json.dumps({
            "status": "success",
            "question": question,
            "answer": answer,
            "top_k": top_k
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Medical QA Assistant')
    parser.add_argument('--question', type=str, help='Question to ask')
    parser.add_argument('--top_k', type=int, default=5, help='Number of top results')
    parser.add_argument('--api', action='store_true', help='Run in API mode')
    
    args = parser.parse_args()
    
    if args.api and args.question:
        # API mode for backend integration
        result = run_api_mode(args.question, args.top_k)
        print(result)
    elif args.question:
        # Single question mode
        answer = ask_question(args.question, args.top_k)
        print(f"Question: {args.question}")
        print(f"Answer: {answer}")
    else:
        # Interactive mode
        print("\n=== 🩺 Medical QA Assistant (Groq + DPR + FAISS) ===\n")
        print("Type your medical question below. Type 'exit' to quit.\n")
        
        while True:
            question = input("💬 Enter your question: ").strip()
            if question.lower() == "exit":
                print("Exiting... Stay healthy! 🫶")
                break
            
            final_answer = ask_question(question)
            print("\n🩺 Question:", question)
            print("\n💬 Answer:", final_answer)
            print("\n" + "-" * 60 + "\n")