#!/usr/bin/env python3
"""
Dedicated QA Model Server
Runs as a separate process to handle medical question answering
"""

import os
import sys
import json
import time
import socket
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Environment setup
from dotenv import load_dotenv
load_dotenv()

# Core imports
import numpy as np
import pandas as pd

# Optional imports with fallbacks
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    import torch
    from transformers import DPRQuestionEncoder, DPRQuestionEncoderTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

class MedicalQAServer:
    def __init__(self, port=5001):
        self.port = port
        self.is_ready = False
        self.docs = []
        self.encoded_docs = None
        self.index = None
        self.question_encoder = None
        self.question_tokenizer = None
        self.groq_client = None
        self.device = "cuda" if TRANSFORMERS_AVAILABLE and torch.cuda.is_available() else "cpu"
        
        # Initialize the QA system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize all QA system components"""
        print("[QA_SERVER] Starting Medical QA System initialization...")
        
        # Step 1: Load medical data
        self._load_medical_data()
        
        # Step 2: Load embeddings and FAISS index
        if FAISS_AVAILABLE:
            self._load_embeddings()
        
        # Step 3: Load DPR encoders
        if TRANSFORMERS_AVAILABLE:
            self._load_dpr_encoders()
        
        # Step 4: Setup Groq client
        self._setup_groq()
        
        print(f"[QA_SERVER] System ready with {len(self.docs)} medical documents")
        self.is_ready = True
    
    def _load_medical_data(self):
        """Load medical QA data from repository files"""
        data_paths = [
            project_root / "data" / "medquad_processed.csv",
            project_root / "data" / "medquad.csv"
        ]
        
        for csv_path in data_paths:
            if csv_path.exists():
                try:
                    print(f"[QA_SERVER] Loading data from {csv_path}")
                    df = pd.read_csv(csv_path)
                    
                    # Try different column names
                    if 'answer_clean' in df.columns:
                        self.docs = df['answer_clean'].astype(str).tolist()
                    elif 'answer' in df.columns:
                        self.docs = df['answer'].astype(str).tolist()
                    elif len(df.columns) >= 2:
                        self.docs = df.iloc[:, 1].astype(str).tolist()
                    
                    # Remove empty or invalid entries
                    self.docs = [doc for doc in self.docs if doc and doc.strip() and doc != 'nan']
                    
                    print(f"[QA_SERVER] Loaded {len(self.docs)} medical documents")
                    return
                    
                except Exception as e:
                    print(f"[QA_SERVER] Error reading {csv_path}: {e}")
                    continue
        
        raise Exception("No medical data files found. Please ensure medquad_processed.csv exists in data/")
    
    def _load_embeddings(self):
        """Load pre-computed embeddings and create FAISS index"""
        embedding_paths = [
            project_root / "embeddings" / "encoded_docs.npy",
            project_root / "embeddings" / "kg_rag_artifacts" / "corpus_embeddings.npy"
        ]
        
        for emb_path in embedding_paths:
            if emb_path.exists():
                try:
                    print(f"[QA_SERVER] Loading embeddings from {emb_path}")
                    self.encoded_docs = np.load(emb_path)
                    
                    # Normalize embeddings
                    self.encoded_docs = self.encoded_docs / np.linalg.norm(
                        self.encoded_docs, axis=1, keepdims=True
                    )
                    
                    # Create FAISS index
                    dimension = self.encoded_docs.shape[1]
                    self.index = faiss.IndexFlatIP(dimension)
                    self.index.add(self.encoded_docs.astype('float32'))
                    
                    print(f"[QA_SERVER] FAISS index built with {self.encoded_docs.shape[0]} embeddings")
                    return
                    
                except Exception as e:
                    print(f"[QA_SERVER] Error loading embeddings: {e}")
                    continue
        
        print("[QA_SERVER] No embeddings found, using text matching fallback")
    
    def _load_dpr_encoders(self):
        """Load DPR question encoder"""
        try:
            print("[QA_SERVER] Loading DPR question encoder...")
            self.question_encoder = DPRQuestionEncoder.from_pretrained(
                "facebook/dpr-question_encoder-single-nq-base"
            ).to(self.device)
            self.question_tokenizer = DPRQuestionEncoderTokenizer.from_pretrained(
                "facebook/dpr-question_encoder-single-nq-base"
            )
            print("[QA_SERVER] DPR encoders loaded successfully")
        except Exception as e:
            print(f"[QA_SERVER] Could not load DPR encoders: {e}")
    
    def _setup_groq(self):
        """Setup Groq API client"""
        api_key = os.getenv("GROQ_API_KEY")
        if api_key and GROQ_AVAILABLE:
            try:
                self.groq_client = Groq(api_key=api_key)
                print("[QA_SERVER] Groq client configured")
            except Exception as e:
                print(f"[QA_SERVER] Groq setup failed: {e}")
    
    def retrieve_context(self, question, top_k=5):
        """Retrieve relevant context using available methods"""
        if not self.docs:
            return "No medical information available."
        
        # Method 1: Use DPR + FAISS if available
        if (self.question_encoder and self.question_tokenizer and 
            self.index and TRANSFORMERS_AVAILABLE):
            try:
                inputs = self.question_tokenizer(
                    question, return_tensors="pt", truncation=True, max_length=512
                ).to(self.device)
                
                with torch.no_grad():
                    q_emb = self.question_encoder(**inputs).pooler_output.cpu().numpy()
                    q_emb = q_emb / np.linalg.norm(q_emb, axis=1, keepdims=True)
                
                scores, indices = self.index.search(q_emb.astype('float32'), min(top_k, len(self.docs)))
                retrieved_texts = [self.docs[i] for i in indices[0] if i < len(self.docs)]
                return " ".join(retrieved_texts)
            except Exception:
                pass
        
        # Method 2: Simple text matching fallback
        question_words = question.lower().split()
        relevant_docs = []
        
        for doc in self.docs:
            doc_lower = doc.lower()
            match_score = sum(1 for word in question_words if word in doc_lower)
            if match_score > 0:
                relevant_docs.append((doc, match_score))
        
        relevant_docs.sort(key=lambda x: x[1], reverse=True)
        selected_docs = [doc for doc, _ in relevant_docs[:top_k]]
        return " ".join(selected_docs) if selected_docs else self.docs[0]
    
    def generate_answer(self, question, context):
        """Generate answer using Groq API or fallback"""
        if self.groq_client:
            prompt = f"""You are a medical AI assistant. Provide a clear, educational answer based on the medical context provided.

Context: {context[:1500]}

Question: {question}

Answer (educational purposes only):"""
            
            try:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=400,
                )
                return response.choices[0].message.content.strip()
            except Exception:
                pass
        
        # Fallback response
        context_snippet = context[:300] + "..." if len(context) > 300 else context
        return f"Based on medical literature: {context_snippet}\n\nNote: This information is for educational purposes. Consult healthcare providers for medical advice."
    
    def process_question(self, question):
        """Process a medical question and return structured response"""
        if not self.is_ready:
            return {
                "status": "error",
                "message": "QA system is still initializing"
            }
        
        try:
            context = self.retrieve_context(question)
            answer = self.generate_answer(question, context)
            
            return {
                "status": "success",
                "question": question,
                "answer": answer,
                "model": "QA Server",
                "method": "dpr_faiss" if self.index else "text_matching"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

class QARequestHandler(BaseHTTPRequestHandler):
    def __init__(self, qa_server, *args, **kwargs):
        self.qa_server = qa_server
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        if self.path == '/ask':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                question = data.get('question', '').strip()
                if not question:
                    self._send_error(400, "Question is required")
                    return
                
                result = self.qa_server.process_question(question)
                self._send_json_response(result)
                
            except Exception as e:
                self._send_error(500, str(e))
        else:
            self._send_error(404, "Not found")
    
    def do_GET(self):
        if self.path == '/health':
            health_data = {
                "service": "QA Server",
                "status": "ready" if self.qa_server.is_ready else "initializing",
                "documents": len(self.qa_server.docs),
                "embeddings": self.qa_server.encoded_docs is not None,
                "dpr_available": self.qa_server.question_encoder is not None,
                "groq_available": self.qa_server.groq_client is not None
            }
            self._send_json_response(health_data)
        else:
            self._send_error(404, "Not found")
    
    def _send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _send_error(self, code, message):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_data = {"error": message, "code": code}
        self.wfile.write(json.dumps(error_data).encode('utf-8'))
    
    def log_message(self, format, *args):
        # Suppress default HTTP server logging
        pass

def main():
    port = int(os.getenv('QA_SERVER_PORT', 5001))
    
    print(f"[QA_SERVER] Initializing Medical QA Server on port {port}...")
    qa_server = MedicalQAServer(port)
    
    # Create HTTP server
    handler = lambda *args, **kwargs: QARequestHandler(qa_server, *args, **kwargs)
    httpd = HTTPServer(('localhost', port), handler)
    
    print(f"[QA_SERVER] QA Server ready on http://localhost:{port}")
    print(f"[QA_SERVER] Health check: http://localhost:{port}/health")
    print(f"[QA_SERVER] Ask endpoint: POST http://localhost:{port}/ask")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("[QA_SERVER] Shutting down QA server...")
        httpd.shutdown()

if __name__ == "__main__":
    main()