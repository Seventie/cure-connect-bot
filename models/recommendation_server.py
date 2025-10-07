#!/usr/bin/env python3
"""
Dedicated Medical Recommendation Server
Runs as a separate process to handle medicine recommendations
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
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

class MedicalRecommendationServer:
    def __init__(self, port=5002):
        self.port = port
        self.is_ready = False
        self.drugs_data = []
        self.knowledge_graph = None
        self.sentence_model = None
        self.corpus_embeddings = None
        self.groq_client = None
        self.nlp = None
        
        # Initialize the recommendation system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize all recommendation system components"""
        print("[REC_SERVER] Starting Medical Recommendation System initialization...")
        
        # Step 1: Load drugs data
        self._load_drugs_data()
        
        # Step 2: Load knowledge graph
        if NETWORKX_AVAILABLE:
            self._load_knowledge_graph()
        
        # Step 3: Load sentence transformer model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self._load_sentence_model()
        
        # Step 4: Load corpus embeddings
        self._load_corpus_embeddings()
        
        # Step 5: Setup Groq client
        self._setup_groq()
        
        # Step 6: Load NLP model for NER
        if SPACY_AVAILABLE:
            self._load_spacy()
        
        print(f"[REC_SERVER] System ready with {len(self.drugs_data)} drug records")
        self.is_ready = True
    
    def _load_drugs_data(self):
        """Load drugs and side effects data from repository files"""
        data_path = project_root / "data" / "drugs_side_effects.csv"
        
        if not data_path.exists():
            raise Exception(f"Drugs data file not found: {data_path}")
        
        try:
            print(f"[REC_SERVER] Loading drugs data from {data_path}")
            df = pd.read_csv(data_path)
            
            # Convert to list of dictionaries for easier processing
            for _, row in df.iterrows():
                drug_record = {
                    'drug_name': str(row.iloc[0]) if len(row) > 0 else '',
                    'medical_condition': str(row.iloc[1]) if len(row) > 1 else '',
                    'side_effects': str(row.iloc[2]) if len(row) > 2 else ''
                }
                
                # Only add records with valid drug names
                if drug_record['drug_name'] and drug_record['drug_name'] != 'nan':
                    self.drugs_data.append(drug_record)
            
            print(f"[REC_SERVER] Loaded {len(self.drugs_data)} drug records")
            
        except Exception as e:
            raise Exception(f"Error loading drugs data: {e}")
    
    def _load_knowledge_graph(self):
        """Load medical knowledge graph if available"""
        kg_paths = [
            project_root / "visualizations" / "medical_kg.graphml",
            project_root / "embeddings" / "kg_rag_artifacts" / "medical_kg.graphml"
        ]
        
        for kg_path in kg_paths:
            if kg_path.exists():
                try:
                    print(f"[REC_SERVER] Loading knowledge graph from {kg_path}")
                    self.knowledge_graph = nx.read_graphml(kg_path)
                    print(f"[REC_SERVER] Knowledge graph loaded with {self.knowledge_graph.number_of_nodes()} nodes")
                    return
                except Exception as e:
                    print(f"[REC_SERVER] Error loading knowledge graph: {e}")
                    continue
        
        print("[REC_SERVER] No knowledge graph found, using text-based matching")
    
    def _load_sentence_model(self):
        """Load sentence transformer model for semantic similarity"""
        try:
            print("[REC_SERVER] Loading sentence transformer model...")
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("[REC_SERVER] Sentence transformer model loaded")
        except Exception as e:
            print(f"[REC_SERVER] Could not load sentence transformer: {e}")
    
    def _load_corpus_embeddings(self):
        """Load pre-computed corpus embeddings"""
        embedding_paths = [
            project_root / "embeddings" / "corpus_embeddings.npy",
            project_root / "embeddings" / "kg_rag_artifacts" / "corpus_embeddings.npy"
        ]
        
        for emb_path in embedding_paths:
            if emb_path.exists():
                try:
                    print(f"[REC_SERVER] Loading corpus embeddings from {emb_path}")
                    self.corpus_embeddings = np.load(emb_path)
                    print(f"[REC_SERVER] Corpus embeddings loaded: {self.corpus_embeddings.shape}")
                    return
                except Exception as e:
                    print(f"[REC_SERVER] Error loading embeddings: {e}")
                    continue
        
        print("[REC_SERVER] No corpus embeddings found")
    
    def _setup_groq(self):
        """Setup Groq API client"""
        api_key = os.getenv("GROQ_API_KEY")
        if api_key and GROQ_AVAILABLE:
            try:
                self.groq_client = Groq(api_key=api_key)
                print("[REC_SERVER] Groq client configured")
            except Exception as e:
                print(f"[REC_SERVER] Groq setup failed: {e}")
    
    def _load_spacy(self):
        """Load spaCy NLP model for NER"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("[REC_SERVER] spaCy NLP model loaded")
        except Exception as e:
            print(f"[REC_SERVER] Could not load spaCy model: {e}")
    
    def extract_medical_entities(self, symptoms_text):
        """Extract medical entities from symptoms text"""
        if self.nlp:
            try:
                doc = self.nlp(symptoms_text)
                entities = [(ent.text, ent.label_) for ent in doc.ents]
                return entities
            except Exception:
                pass
        
        # Fallback: simple tokenization
        return [(word, 'SYMPTOM') for word in symptoms_text.split()]
    
    def find_recommendations(self, symptoms, additional_info="", top_k=5):
        """Find medicine recommendations based on symptoms"""
        if not self.is_ready:
            return {
                "status": "error",
                "message": "Recommendation system is still initializing"
            }
        
        try:
            # Extract entities from symptoms
            symptoms_text = " ".join(symptoms) + " " + additional_info
            entities = self.extract_medical_entities(symptoms_text)
            
            # Find matching drugs
            recommendations = []
            
            for drug in self.drugs_data:
                match_score = 0
                matched_symptoms = []
                
                # Check for symptom matches in conditions
                condition_lower = drug['medical_condition'].lower()
                
                for symptom in symptoms:
                    symptom_lower = symptom.lower()
                    if (symptom_lower in condition_lower or 
                        any(word in condition_lower for word in symptom_lower.split())):
                        match_score += 1
                        matched_symptoms.append(symptom)
                
                if match_score > 0:
                    confidence = min(0.95, 0.6 + (match_score * 0.1))
                    recommendations.append({
                        'drug_name': drug['drug_name'],
                        'condition': drug['medical_condition'],
                        'side_effects': drug['side_effects'],
                        'matched_symptoms': matched_symptoms,
                        'confidence_score': confidence,
                        'match_score': match_score
                    })
            
            # Sort by match score and confidence
            recommendations.sort(key=lambda x: (x['match_score'], x['confidence_score']), reverse=True)
            
            # Generate AI explanation if Groq is available
            ai_explanation = self._generate_explanation(symptoms, recommendations[:3])
            
            return {
                "status": "success",
                "symptoms": symptoms,
                "additional_info": additional_info,
                "recommendations": recommendations[:top_k],
                "entities_extracted": entities,
                "ai_explanation": ai_explanation,
                "total_matches": len(recommendations)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _generate_explanation(self, symptoms, top_recommendations):
        """Generate AI explanation for recommendations"""
        if not self.groq_client or not top_recommendations:
            return "Recommendations based on symptom-condition matching from medical database."
        
        try:
            symptoms_text = ", ".join(symptoms)
            drugs_text = ", ".join([rec['drug_name'] for rec in top_recommendations])
            
            prompt = f"""Based on the symptoms: {symptoms_text}

The following medicines were recommended: {drugs_text}

Provide a brief, educational explanation (2-3 sentences) about why these medicines might be suggested for these symptoms. Focus on general medical principles.

Explanation:"""
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
            )
            return response.choices[0].message.content.strip()
            
        except Exception:
            return "AI explanation temporarily unavailable. Recommendations based on medical database matching."
    
    def search_drugs(self, query, limit=10):
        """Search drugs by name, condition, or side effects"""
        if not self.is_ready:
            return {
                "status": "error", 
                "message": "System not ready"
            }
        
        query_lower = query.lower()
        results = []
        
        for drug in self.drugs_data:
            match_score = 0
            match_type = ""
            
            # Check drug name
            if query_lower in drug['drug_name'].lower():
                match_score = 0.9
                match_type = "drug_name"
            # Check condition
            elif query_lower in drug['medical_condition'].lower():
                match_score = 0.7
                match_type = "condition"
            # Check side effects
            elif query_lower in drug['side_effects'].lower():
                match_score = 0.5
                match_type = "side_effect"
            
            if match_score > 0:
                results.append({
                    **drug,
                    'match_score': match_score,
                    'match_type': match_type
                })
        
        # Sort by match score
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        return {
            "status": "success",
            "query": query,
            "results": results[:limit],
            "total_found": len(results)
        }

class RecommendationRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, rec_server, *args, **kwargs):
        self.rec_server = rec_server
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        if self.path == '/recommend':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                symptoms = data.get('symptoms', [])
                additional_info = data.get('additional_info', '')
                top_k = data.get('top_k', 5)
                
                if not symptoms or not isinstance(symptoms, list):
                    self._send_error(400, "Symptoms array is required")
                    return
                
                result = self.rec_server.find_recommendations(symptoms, additional_info, top_k)
                self._send_json_response(result)
                
            except Exception as e:
                self._send_error(500, str(e))
        else:
            self._send_error(404, "Not found")
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/health':
            health_data = {
                "service": "Recommendation Server",
                "status": "ready" if self.rec_server.is_ready else "initializing",
                "drugs_count": len(self.rec_server.drugs_data),
                "knowledge_graph": self.rec_server.knowledge_graph is not None,
                "sentence_model": self.rec_server.sentence_model is not None,
                "groq_available": self.rec_server.groq_client is not None
            }
            self._send_json_response(health_data)
            
        elif parsed_path.path == '/search':
            query_params = parse_qs(parsed_path.query)
            query = query_params.get('q', [''])[0]
            limit = int(query_params.get('limit', [10])[0])
            
            if not query:
                self._send_error(400, "Query parameter 'q' is required")
                return
            
            result = self.rec_server.search_drugs(query, limit)
            self._send_json_response(result)
            
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
    port = int(os.getenv('REC_SERVER_PORT', 5002))
    
    print(f"[REC_SERVER] Initializing Medical Recommendation Server on port {port}...")
    rec_server = MedicalRecommendationServer(port)
    
    # Create HTTP server
    handler = lambda *args, **kwargs: RecommendationRequestHandler(rec_server, *args, **kwargs)
    httpd = HTTPServer(('localhost', port), handler)
    
    print(f"[REC_SERVER] Recommendation Server ready on http://localhost:{port}")
    print(f"[REC_SERVER] Health check: http://localhost:{port}/health")
    print(f"[REC_SERVER] Recommend endpoint: POST http://localhost:{port}/recommend")
    print(f"[REC_SERVER] Search endpoint: GET http://localhost:{port}/search?q=query")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("[REC_SERVER] Shutting down recommendation server...")
        httpd.shutdown()

if __name__ == "__main__":
    main()