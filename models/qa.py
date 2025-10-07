#!/usr/bin/env python3
"""
Medical QA Pipeline with Groq and FAISS
Improved version with robust error handling and flexible file paths
"""

import os
import sys
import json
import argparse
import traceback
import numpy as np
import pandas as pd
from pathlib import Path

# Environment setup
from dotenv import load_dotenv
load_dotenv()

# Optional imports with fallbacks
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    print("[WARN] FAISS not available. Installing: pip install faiss-cpu")
    FAISS_AVAILABLE = False

try:
    import torch
    from transformers import DPRQuestionEncoder, DPRQuestionEncoderTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("[WARN] Transformers not available. Installing: pip install transformers torch")
    TRANSFORMERS_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    print("[WARN] Groq not available. Installing: pip install groq")
    GROQ_AVAILABLE = False

class MedicalQASystem:
    """
    Medical Question Answering System with multiple fallback levels
    """
    
    def __init__(self, data_dir="data", embeddings_dir="embeddings"):
        self.data_dir = Path(data_dir)
        self.embeddings_dir = Path(embeddings_dir)
        self.docs = []
        self.encoded_docs = None
        self.index = None
        self.question_encoder = None
        self.question_tokenizer = None
        self.groq_client = None
        self.device = "cuda" if TRANSFORMERS_AVAILABLE and torch.cuda.is_available() else "cpu"
        
        self._load_system()
    
    def _load_system(self):
        """Initialize the QA system with available components"""
        print("[INIT] Loading Medical QA System...")
        
        # Load data
        self._load_data()
        
        # Load embeddings and FAISS index
        if FAISS_AVAILABLE:
            self._load_embeddings()
        
        # Load DPR encoders
        if TRANSFORMERS_AVAILABLE:
            self._load_dpr_encoders()
        
        # Setup Groq client
        self._setup_groq()
        
        print(f"[INIT] System ready with {len(self.docs)} documents")
    
    def _load_data(self):
        """Load medical QA data from CSV"""
        csv_files = [
            self.data_dir / "medquad_processed.csv",
            "data/medquad_processed.csv",
            "../data/medquad_processed.csv"
        ]
        
        for csv_path in csv_files:
            if Path(csv_path).exists():
                try:
                    df = pd.read_csv(csv_path)
                    if 'answer_clean' in df.columns:
                        self.docs = df['answer_clean'].astype(str).tolist()
                    elif 'answer' in df.columns:
                        self.docs = df['answer'].astype(str).tolist()
                    elif len(df.columns) >= 2:
                        self.docs = df.iloc[:, 1].astype(str).tolist()  # Use second column
                    else:
                        self.docs = df.iloc[:, 0].astype(str).tolist()  # Use first column
                    
                    print(f"[INFO] Loaded {len(self.docs)} documents from {csv_path}")
                    return
                except Exception as e:
                    print(f"[WARN] Error reading {csv_path}: {e}")
                    continue
        
        # Fallback: create dummy data
        print("[WARN] No data file found. Using fallback medical responses.")
        self.docs = [
            "Fever can be managed with rest, hydration, and over-the-counter medications like acetaminophen.",
            "Headaches may be caused by stress, dehydration, or underlying medical conditions.",
            "Regular exercise and a balanced diet are important for maintaining good health.",
            "Consult a healthcare provider for persistent symptoms or medical concerns.",
            "Preventive care includes regular check-ups and following medical guidelines."
        ]
    
    def _load_embeddings(self):
        """Load pre-computed embeddings and create FAISS index"""
        embedding_files = [
            self.embeddings_dir / "encoded_docs.npy",
            "embeddings/encoded_docs.npy",
            "../embeddings/encoded_docs.npy"
        ]
        
        for emb_path in embedding_files:
            if Path(emb_path).exists():
                try:
                    self.encoded_docs = np.load(emb_path)
                    # Normalize embeddings
                    self.encoded_docs = self.encoded_docs / np.linalg.norm(
                        self.encoded_docs, axis=1, keepdims=True
                    )
                    
                    # FIX: FAISS dimension bug - get dimension as int, not tuple
                    dimension = self.encoded_docs.shape[1]  # Fixed: was shape, now shape[1]
                    self.index = faiss.IndexFlatIP(dimension)
                    self.index.add(self.encoded_docs.astype('float32'))
                    
                    print(f"[INFO] FAISS index built with {self.encoded_docs.shape[0]} documents")
                    return
                except Exception as e:
                    print(f"[WARN] Error loading embeddings from {emb_path}: {e}")
                    continue
        
        # Create dummy embeddings if none found
        print("[WARN] No embeddings found. Creating dummy embeddings for testing.")
        dimension = 768
        self.encoded_docs = np.random.rand(len(self.docs), dimension).astype('float32')
        self.encoded_docs = self.encoded_docs / np.linalg.norm(
            self.encoded_docs, axis=1, keepdims=True
        )
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(self.encoded_docs)
    
    def _load_dpr_encoders(self):
        """Load DPR question encoder"""
        try:
            print("[INIT] Loading DPR question encoder...")
            self.question_encoder = DPRQuestionEncoder.from_pretrained(
                "facebook/dpr-question_encoder-single-nq-base"
            ).to(self.device)
            self.question_tokenizer = DPRQuestionEncoderTokenizer.from_pretrained(
                "facebook/dpr-question_encoder-single-nq-base"
            )
            print("[INFO] DPR encoders loaded successfully")
        except Exception as e:
            print(f"[WARN] Could not load DPR encoders: {e}")
            self.question_encoder = None
            self.question_tokenizer = None
    
    def _setup_groq(self):
        """Setup Groq API client"""
        api_key = os.getenv("GROQ_API_KEY")
        if api_key and api_key != "your-groq-api-key-here" and GROQ_AVAILABLE:
            try:
                self.groq_client = Groq(api_key=api_key)
                print("[INFO] Groq client configured successfully")
            except Exception as e:
                print(f"[WARN] Could not setup Groq client: {e}")
                self.groq_client = None
        else:
            print("[WARN] Groq API key not configured or Groq not available")
    
    def retrieve_context(self, question: str, top_k: int = 5) -> str:
        """Retrieve relevant context using FAISS or fallback methods"""
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
                
                # FIX: FAISS search indices handling - flatten indices and map to docs
                idx_list = indices[0].tolist()  # Fixed: was iterating 2D array directly
                retrieved_texts = [self.docs[i] for i in idx_list if i < len(self.docs)]
                return " ".join(retrieved_texts)
                
            except Exception as e:
                print(f"[WARN] Error in FAISS retrieval: {e}")
        
        # Method 2: Simple text matching fallback
        return self._simple_text_retrieval(question, top_k)
    
    def _simple_text_retrieval(self, question: str, top_k: int) -> str:
        """Simple keyword-based text retrieval"""
        question_words = question.lower().split()
        relevant_docs = []
        
        for doc in self.docs:
            doc_lower = doc.lower()
            match_score = sum(1 for word in question_words if word in doc_lower)
            if match_score > 0:
                relevant_docs.append((doc, match_score))
        
        # FIX: Sort by relevance correctly using lambda x: x[1] to sort by score
        relevant_docs.sort(key=lambda x: x[1], reverse=True)  # Fixed: was key=lambda x: x
        selected_docs = [doc for doc, _ in relevant_docs[:top_k]]
        
        # FIX: Return joined string when no matches, not list
        return " ".join(selected_docs) if selected_docs else " ".join(self.docs[:1])  # Fixed: was returning self.docs
    
    def generate_answer(self, question: str, context: str) -> str:
        """Generate answer using Groq API or fallback"""
        if self.groq_client:
            return self._generate_with_groq(question, context)
        else:
            return self._generate_fallback(question, context)
    
    def _generate_with_groq(self, question: str, context: str) -> str:
        """Generate answer using Groq API"""
        prompt = f"""You are a knowledgeable medical assistant for educational purposes.

Context: {context}

Question: {question}

Provide a clear, educational answer based on the context above. If the context doesn't fully answer the question, use your medical knowledge to provide helpful information. Keep the response informative but accessible.

Answer:"""
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
            )
            # FIX: Groq message extraction - access first choice correctly
            return response.choices[0].message.content.strip()  # Fixed: was response.choices.message.content
        except Exception as e:
            print(f"[WARN] Groq API error: {e}")
            return self._generate_fallback(question, context)
    
    def _generate_fallback(self, question: str, context: str) -> str:
        """Fallback answer generation without external APIs"""
        # Simple template-based response
        context_snippet = context[:200] + "..." if len(context) > 200 else context
        return f"Based on available medical information: {context_snippet} \n\nThis information is provided for educational purposes. For specific medical concerns, please consult with a healthcare professional."
    
    def ask_question(self, question: str, top_k: int = 5) -> dict:
        """Main function to process questions and return structured response"""
        try:
            if not question or not question.strip():
                return {
                    "status": "error",
                    "message": "Empty question provided"
                }
            
            # Retrieve context
            context = self.retrieve_context(question, top_k)
            
            # Generate answer
            answer = self.generate_answer(question, context)
            
            return {
                "status": "success",
                "question": question,
                "answer": answer,
                "context_used": len(context.split()[:50]),  # First 50 words
                "retrieval_method": "dpr_faiss" if (self.question_encoder and self.index) else "text_matching",
                "generation_method": "groq" if self.groq_client else "template"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing question: {str(e)}",
                "traceback": traceback.format_exc() if os.getenv("DEBUG") == "true" else None
            }

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Medical QA Assistant')
    parser.add_argument('--question', type=str, help='Question to ask')
    parser.add_argument('--top_k', type=int, default=5, help='Number of top results')
    parser.add_argument('--api', action='store_true', help='Run in API mode')
    parser.add_argument('--data_dir', type=str, default='data', help='Data directory')
    parser.add_argument('--embeddings_dir', type=str, default='embeddings', help='Embeddings directory')
    
    args = parser.parse_args()
    
    # Initialize QA system
    try:
        qa_system = MedicalQASystem(args.data_dir, args.embeddings_dir)
    except Exception as e:
        if args.api:
            print(json.dumps({
                "status": "error",
                "message": f"Failed to initialize QA system: {str(e)}"
            }))
        else:
            print(f"Error initializing QA system: {e}")
        sys.exit(1)
    
    if args.api and args.question:
        # API mode for backend integration
        result = qa_system.ask_question(args.question, args.top_k)
        print(json.dumps(result))
    elif args.question:
        # Single question mode
        result = qa_system.ask_question(args.question, args.top_k)
        if result["status"] == "success":
            print(f"Question: {result['question']}")
            print(f"Answer: {result['answer']}")
        else:
            print(f"Error: {result['message']}")
    else:
        # Interactive mode
        print("\n" + "=" * 60)
        print("🩺 MEDICAL QA ASSISTANT")
        print("=" * 60)
        print("Ask medical questions for educational information.")
        print("Type 'exit' to quit.\n")
        
        while True:
            try:
                question = input("💬 Enter your question: ").strip()
                if question.lower() in ['exit', 'quit', 'q']:
                    print("Goodbye! Stay healthy! 🚀")
                    break
                
                if not question:
                    continue
                
                result = qa_system.ask_question(question)
                if result["status"] == "success":
                    print(f"\n🩺 Answer: {result['answer']}")
                    print(f"🔍 Method: {result['retrieval_method']} + {result['generation_method']}")
                else:
                    print(f"\n❌ Error: {result['message']}")
                
                print("\n" + "-" * 60 + "\n")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()