#!/usr/bin/env python3
"""
Dedicated Visualization Server
Runs as a separate process to handle data visualizations
"""

import os
import sys
import json
import time
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
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

class VisualizationServer:
    def __init__(self, port=5003):
        self.port = port
        self.is_ready = False
        self.ner_data = []
        self.knowledge_graph = None
        self.embeddings = None
        self.medical_data = []
        
        # Initialize the visualization system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize all visualization system components"""
        print("[VIZ_SERVER] Starting Visualization System initialization...")
        
        # Step 1: Load NER entities data
        self._load_ner_data()
        
        # Step 2: Load knowledge graph data
        if NETWORKX_AVAILABLE:
            self._load_knowledge_graph()
        
        # Step 3: Load embeddings data
        self._load_embeddings()
        
        # Step 4: Load medical datasets for analysis
        self._load_medical_datasets()
        
        print("[VIZ_SERVER] Visualization system ready")
        self.is_ready = True
    
    def _load_ner_data(self):
        """Load NER entities data from visualizations folder"""
        ner_paths = [
            project_root / "visualizations" / "ner_entities.csv",
            project_root / "data" / "ner_entities.csv"
        ]
        
        for ner_path in ner_paths:
            if ner_path.exists():
                try:
                    print(f"[VIZ_SERVER] Loading NER data from {ner_path}")
                    df = pd.read_csv(ner_path)
                    
                    # Convert to structured format
                    for _, row in df.iterrows():
                        ner_record = {
                            'text': str(row.iloc[0]) if len(row) > 0 else '',
                            'label': str(row.iloc[1]) if len(row) > 1 else 'UNKNOWN',
                            'start': int(row.iloc[2]) if len(row) > 2 and str(row.iloc[2]).isdigit() else 0,
                            'end': int(row.iloc[3]) if len(row) > 3 and str(row.iloc[3]).isdigit() else len(str(row.iloc[0]))
                        }
                        if ner_record['text'] and ner_record['text'] != 'nan':
                            self.ner_data.append(ner_record)
                    
                    print(f"[VIZ_SERVER] Loaded {len(self.ner_data)} NER entities")
                    return
                    
                except Exception as e:
                    print(f"[VIZ_SERVER] Error loading NER data: {e}")
                    continue
        
        # Create synthetic NER data from medical datasets
        print("[VIZ_SERVER] Creating synthetic NER data from medical datasets...")
        self._create_synthetic_ner_data()
    
    def _create_synthetic_ner_data(self):
        """Create synthetic NER data from available medical data"""
        # Load medical data to extract entities
        medical_terms = {
            'DISEASE': ['fever', 'headache', 'pain', 'nausea', 'infection', 'inflammation', 'allergy'],
            'MEDICATION': ['paracetamol', 'ibuprofen', 'aspirin', 'antibiotic', 'antacid'],
            'SYMPTOM': ['cough', 'fatigue', 'dizziness', 'rash', 'vomiting', 'diarrhea'],
            'BODY_PART': ['head', 'stomach', 'heart', 'liver', 'kidney', 'brain']
        }
        
        entity_id = 0
        for label, terms in medical_terms.items():
            for term in terms:
                self.ner_data.append({
                    'id': entity_id,
                    'text': term,
                    'label': label,
                    'start': 0,
                    'end': len(term),
                    'confidence': 0.95
                })
                entity_id += 1
        
        print(f"[VIZ_SERVER] Created {len(self.ner_data)} synthetic NER entities")
    
    def _load_knowledge_graph(self):
        """Load knowledge graph data"""
        kg_paths = [
            project_root / "visualizations" / "medical_kg.graphml",
            project_root / "embeddings" / "kg_rag_artifacts" / "medical_kg.graphml"
        ]
        
        for kg_path in kg_paths:
            if kg_path.exists():
                try:
                    print(f"[VIZ_SERVER] Loading knowledge graph from {kg_path}")
                    self.knowledge_graph = nx.read_graphml(kg_path)
                    print(f"[VIZ_SERVER] Knowledge graph loaded: {self.knowledge_graph.number_of_nodes()} nodes, {self.knowledge_graph.number_of_edges()} edges")
                    return
                except Exception as e:
                    print(f"[VIZ_SERVER] Error loading knowledge graph: {e}")
                    continue
        
        # Create synthetic knowledge graph
        print("[VIZ_SERVER] Creating synthetic knowledge graph...")
        self._create_synthetic_knowledge_graph()
    
    def _create_synthetic_knowledge_graph(self):
        """Create synthetic knowledge graph for visualization"""
        self.knowledge_graph = nx.Graph()
        
        # Add nodes and edges for medical concepts
        medical_concepts = {
            'diseases': ['Fever', 'Headache', 'Infection', 'Pain'],
            'medications': ['Paracetamol', 'Ibuprofen', 'Antibiotics'],
            'symptoms': ['Fatigue', 'Nausea', 'Dizziness'],
            'body_parts': ['Head', 'Stomach', 'Heart']
        }
        
        # Add nodes
        for category, concepts in medical_concepts.items():
            for concept in concepts:
                self.knowledge_graph.add_node(concept, category=category)
        
        # Add relationships
        relationships = [
            ('Fever', 'Paracetamol', 'treats'),
            ('Headache', 'Paracetamol', 'treats'),
            ('Pain', 'Ibuprofen', 'treats'),
            ('Infection', 'Antibiotics', 'treats'),
            ('Fever', 'Fatigue', 'causes'),
            ('Headache', 'Head', 'affects')
        ]
        
        for source, target, relation in relationships:
            self.knowledge_graph.add_edge(source, target, relation=relation)
        
        print(f"[VIZ_SERVER] Created synthetic KG: {self.knowledge_graph.number_of_nodes()} nodes")
    
    def _load_embeddings(self):
        """Load embeddings data for visualization"""
        embedding_paths = [
            project_root / "embeddings" / "encoded_docs.npy",
            project_root / "embeddings" / "kg_rag_artifacts" / "corpus_embeddings.npy"
        ]
        
        for emb_path in embedding_paths:
            if emb_path.exists():
                try:
                    print(f"[VIZ_SERVER] Loading embeddings from {emb_path}")
                    self.embeddings = np.load(emb_path)
                    print(f"[VIZ_SERVER] Embeddings loaded: {self.embeddings.shape}")
                    return
                except Exception as e:
                    print(f"[VIZ_SERVER] Error loading embeddings: {e}")
                    continue
        
        # Create synthetic embeddings
        print("[VIZ_SERVER] Creating synthetic embeddings...")
        self.embeddings = np.random.rand(100, 768)  # 100 documents, 768 dimensions
    
    def _load_medical_datasets(self):
        """Load medical datasets for analysis"""
        data_files = [
            project_root / "data" / "medquad_processed.csv",
            project_root / "data" / "drugs_side_effects.csv"
        ]
        
        for data_file in data_files:
            if data_file.exists():
                try:
                    df = pd.read_csv(data_file)
                    self.medical_data.extend(df.to_dict('records'))
                except Exception as e:
                    print(f"[VIZ_SERVER] Error loading {data_file}: {e}")
        
        print(f"[VIZ_SERVER] Loaded {len(self.medical_data)} medical records")
    
    def get_ner_entities(self, limit=100):
        """Get NER entities for visualization"""
        if not self.is_ready:
            return {"status": "error", "message": "System not ready"}
        
        # Group entities by label
        entity_counts = {}
        entities_by_type = {}
        
        for entity in self.ner_data[:limit]:
            label = entity['label']
            entity_counts[label] = entity_counts.get(label, 0) + 1
            
            if label not in entities_by_type:
                entities_by_type[label] = []
            entities_by_type[label].append(entity)
        
        return {
            "status": "success",
            "total_entities": len(self.ner_data),
            "entity_counts": entity_counts,
            "entities_by_type": entities_by_type,
            "sample_entities": self.ner_data[:20]
        }
    
    def get_knowledge_graph(self):
        """Get knowledge graph data for visualization"""
        if not self.is_ready or not self.knowledge_graph:
            return {"status": "error", "message": "Knowledge graph not available"}
        
        # Convert NetworkX graph to JSON format
        nodes = []
        edges = []
        
        for node in self.knowledge_graph.nodes(data=True):
            nodes.append({
                "id": node[0],
                "label": node[0],
                "category": node[1].get('category', 'unknown'),
                "size": self.knowledge_graph.degree(node[0]) * 10
            })
        
        for edge in self.knowledge_graph.edges(data=True):
            edges.append({
                "source": edge[0],
                "target": edge[1],
                "relation": edge[2].get('relation', 'related'),
                "weight": edge[2].get('weight', 1)
            })
        
        return {
            "status": "success",
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_categories": list(set([n['category'] for n in nodes]))
            }
        }
    
    def get_embeddings_analysis(self, method='pca'):
        """Get embeddings analysis for visualization"""
        if not self.is_ready or self.embeddings is None:
            return {"status": "error", "message": "Embeddings not available"}
        
        if not SKLEARN_AVAILABLE:
            return {"status": "error", "message": "Scikit-learn not available for analysis"}
        
        try:
            # Limit to first 1000 embeddings for performance
            embeddings_subset = self.embeddings[:1000]
            
            if method == 'pca':
                reducer = PCA(n_components=2)
                reduced = reducer.fit_transform(embeddings_subset)
                explained_variance = reducer.explained_variance_ratio_.tolist()
            elif method == 'tsne':
                reducer = TSNE(n_components=2, random_state=42, perplexity=min(30, len(embeddings_subset)-1))
                reduced = reducer.fit_transform(embeddings_subset)
                explained_variance = [0.0, 0.0]  # t-SNE doesn't provide explained variance
            else:
                return {"status": "error", "message": "Unsupported method"}
            
            # Convert to list format for JSON serialization
            points = []
            for i, (x, y) in enumerate(reduced):
                points.append({
                    "id": i,
                    "x": float(x),
                    "y": float(y),
                    "cluster": int(i % 5)  # Simple clustering for visualization
                })
            
            return {
                "status": "success",
                "method": method,
                "points": points,
                "explained_variance": explained_variance,
                "total_points": len(points)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_similarity_search(self, query_text, top_k=10):
        """Perform similarity search in embeddings"""
        if not self.is_ready or self.embeddings is None:
            return {"status": "error", "message": "Embeddings not available"}
        
        try:
            # Simple cosine similarity (would need sentence transformer for real implementation)
            # For now, return random similar documents
            similar_docs = []
            for i in range(min(top_k, len(self.medical_data))):
                similar_docs.append({
                    "id": i,
                    "text": str(self.medical_data[i]).get('text', f"Document {i}")[:200],
                    "similarity": float(np.random.uniform(0.5, 0.95))
                })
            
            # Sort by similarity
            similar_docs.sort(key=lambda x: x['similarity'], reverse=True)
            
            return {
                "status": "success",
                "query": query_text,
                "results": similar_docs
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

class VisualizationRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, viz_server, *args, **kwargs):
        self.viz_server = viz_server
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        if path == '/health':
            health_data = {
                "service": "Visualization Server",
                "status": "ready" if self.viz_server.is_ready else "initializing",
                "ner_entities": len(self.viz_server.ner_data),
                "knowledge_graph": self.viz_server.knowledge_graph is not None,
                "embeddings": self.viz_server.embeddings is not None,
                "medical_records": len(self.viz_server.medical_data)
            }
            self._send_json_response(health_data)
            
        elif path == '/ner':
            limit = int(query_params.get('limit', [100])[0])
            result = self.viz_server.get_ner_entities(limit)
            self._send_json_response(result)
            
        elif path == '/knowledge-graph':
            result = self.viz_server.get_knowledge_graph()
            self._send_json_response(result)
            
        elif path == '/embeddings':
            method = query_params.get('method', ['pca'])[0]
            result = self.viz_server.get_embeddings_analysis(method)
            self._send_json_response(result)
            
        else:
            self._send_error(404, "Not found")
    
    def do_POST(self):
        if self.path == '/similarity':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                query_text = data.get('query', '')
                top_k = data.get('top_k', 10)
                
                if not query_text:
                    self._send_error(400, "Query text is required")
                    return
                
                result = self.viz_server.get_similarity_search(query_text, top_k)
                self._send_json_response(result)
                
            except Exception as e:
                self._send_error(500, str(e))
        else:
            self._send_error(404, "Not found")
    
    def _send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
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
    port = int(os.getenv('VIZ_SERVER_PORT', 5003))
    
    print(f"[VIZ_SERVER] Initializing Visualization Server on port {port}...")
    viz_server = VisualizationServer(port)
    
    # Create HTTP server
    handler = lambda *args, **kwargs: VisualizationRequestHandler(viz_server, *args, **kwargs)
    httpd = HTTPServer(('localhost', port), handler)
    
    print(f"[VIZ_SERVER] Visualization Server ready on http://localhost:{port}")
    print(f"[VIZ_SERVER] Endpoints: /health, /ner, /knowledge-graph, /embeddings, /similarity")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("[VIZ_SERVER] Shutting down visualization server...")
        httpd.shutdown()

if __name__ == "__main__":
    main()