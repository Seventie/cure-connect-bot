#!/usr/bin/env python3
"""
Visualization Server - HTTP wrapper for visualization data
Provides REST API endpoints for medical visualizations
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
ner_data = None
viz_data = None
initialization_status = {"status": "initializing", "message": "Loading visualization data..."}

def initialize_visualization_system():
    """Initialize the visualization system in a separate thread"""
    global ner_data, viz_data, initialization_status
    
    try:
        logger.info("[VIZ_SERVER] Starting visualization system initialization...")
        initialization_status = {"status": "initializing", "message": "Loading visualization data..."}
        
        # Load NER entities data
        ner_paths = [
            Path(__file__).parent.parent / "visualizations" / "ner_entities.csv",
            Path(__file__).parent.parent / "embeddings" / "kg_rag_artifacts" / "ner_entities.csv"
        ]
        
        for ner_path in ner_paths:
            if ner_path.exists():
                try:
                    ner_data = pd.read_csv(ner_path)
                    logger.info(f"[VIZ_SERVER] Loaded {len(ner_data)} NER entities from {ner_path}")
                    break
                except Exception as e:
                    logger.warning(f"[VIZ_SERVER] Error loading NER data from {ner_path}: {e}")
        
        if ner_data is None:
            # Create sample NER data
            ner_data = pd.DataFrame({
                'entity': ['fever', 'headache', 'nausea', 'fatigue', 'cough', 'pain'],
                'label': ['SYMPTOM', 'SYMPTOM', 'SYMPTOM', 'SYMPTOM', 'SYMPTOM', 'SYMPTOM'],
                'frequency': [45, 32, 28, 41, 38, 52]
            })
            logger.info("[VIZ_SERVER] Using sample NER data")
        
        # Load additional visualization data from drugs database
        drugs_path = Path(__file__).parent.parent / "data" / "drugs_side_effects.csv"
        if drugs_path.exists():
            try:
                viz_data = pd.read_csv(drugs_path)
                logger.info(f"[VIZ_SERVER] Loaded {len(viz_data)} drug records for visualization")
            except Exception as e:
                logger.warning(f"[VIZ_SERVER] Error loading drug data: {e}")
        
        initialization_status = {"status": "ready", "message": "Visualization system ready"}
        logger.info("[VIZ_SERVER] Visualization system initialized successfully")
        
    except Exception as e:
        logger.error(f"[VIZ_SERVER] Failed to initialize visualization system: {e}")
        initialization_status = {
            "status": "error", 
            "message": f"Failed to initialize: {str(e)}"
        }

def generate_embeddings_visualization(method='pca'):
    """Generate embeddings visualization data"""
    try:
        # Try to load actual embeddings
        embedding_paths = [
            Path(__file__).parent.parent / "embeddings" / "encoded_docs.npy",
            Path(__file__).parent.parent / "embeddings" / "kg_rag_artifacts" / "corpus_embeddings.npy"
        ]
        
        embeddings = None
        for emb_path in embedding_paths:
            if emb_path.exists():
                try:
                    embeddings = np.load(emb_path)
                    logger.info(f"[VIZ_SERVER] Loaded embeddings from {emb_path}")
                    break
                except Exception as e:
                    logger.warning(f"[VIZ_SERVER] Error loading embeddings from {emb_path}: {e}")
        
        if embeddings is None:
            # Generate sample embeddings for visualization
            embeddings = np.random.rand(100, 384)
            logger.info("[VIZ_SERVER] Using sample embeddings")
        
        # Reduce dimensionality for visualization
        if method == 'pca':
            try:
                from sklearn.decomposition import PCA
                pca = PCA(n_components=2)
                reduced_embeddings = pca.fit_transform(embeddings[:100])  # Limit for performance
            except ImportError:
                # Fallback: use first two dimensions
                reduced_embeddings = embeddings[:100, :2]
        else:
            # Default: use first two dimensions
            reduced_embeddings = embeddings[:100, :2]
        
        # Create visualization data
        viz_points = []
        for i, (x, y) in enumerate(reduced_embeddings):
            viz_points.append({
                'id': i,
                'x': float(x),
                'y': float(y),
                'label': f'Document {i+1}'
            })
        
        return viz_points
        
    except Exception as e:
        logger.error(f"[VIZ_SERVER] Error generating embeddings visualization: {e}")
        return []

def generate_knowledge_graph_data():
    """Generate knowledge graph visualization data"""
    try:
        # Try to load actual knowledge graph
        kg_path = Path(__file__).parent.parent / "visualizations" / "medical_kg.graphml"
        
        if kg_path.exists():
            try:
                import networkx as nx
                G = nx.read_graphml(kg_path)
                
                nodes = []
                edges = []
                
                # Convert to JSON format (limit for performance)
                for node in list(G.nodes())[:50]:  # Limit nodes for performance
                    node_data = G.nodes[node]
                    nodes.append({
                        'id': node,
                        'label': node_data.get('label', node),
                        'type': node_data.get('type', 'unknown')
                    })
                
                for edge in list(G.edges())[:100]:  # Limit edges for performance
                    edge_data = G.edges[edge]
                    edges.append({
                        'source': edge[0],
                        'target': edge[1],
                        'relation': edge_data.get('relation', 'related')
                    })
                
                return {'nodes': nodes, 'edges': edges}
                
            except Exception as e:
                logger.warning(f"[VIZ_SERVER] Error loading knowledge graph: {e}")
        
        # Fallback: create sample knowledge graph
        nodes = [
            {'id': 'fever', 'label': 'Fever', 'type': 'symptom'},
            {'id': 'paracetamol', 'label': 'Paracetamol', 'type': 'drug'},
            {'id': 'headache', 'label': 'Headache', 'type': 'symptom'},
            {'id': 'ibuprofen', 'label': 'Ibuprofen', 'type': 'drug'},
            {'id': 'nausea', 'label': 'Nausea', 'type': 'symptom'}
        ]
        
        edges = [
            {'source': 'fever', 'target': 'paracetamol', 'relation': 'treated_by'},
            {'source': 'headache', 'target': 'paracetamol', 'relation': 'treated_by'},
            {'source': 'headache', 'target': 'ibuprofen', 'relation': 'treated_by'},
            {'source': 'paracetamol', 'target': 'nausea', 'relation': 'may_cause'}
        ]
        
        return {'nodes': nodes, 'edges': edges}
        
    except Exception as e:
        logger.error(f"[VIZ_SERVER] Error generating knowledge graph: {e}")
        return {'nodes': [], 'edges': []}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": initialization_status["status"],
        "message": initialization_status["message"],
        "service": "Visualization Server",
        "port": int(os.getenv('VIZ_SERVER_PORT', 5003)),
        "ner_entities": len(ner_data) if ner_data is not None else 0,
        "viz_records": len(viz_data) if viz_data is not None else 0,
        "timestamp": time.time()
    })

@app.route('/ner', methods=['GET'])
def get_ner_entities():
    """Get NER entities for visualization"""
    if initialization_status["status"] != "ready":
        return jsonify({
            "status": "error",
            "message": "Visualization system not ready yet",
            "initialization_status": initialization_status
        }), 503
    
    try:
        limit = int(request.args.get('limit', 100))
        
        if ner_data is None or ner_data.empty:
            return jsonify({
                "status": "error",
                "message": "No NER data available"
            }), 404
        
        # Get top entities by frequency or first N entities
        if 'frequency' in ner_data.columns:
            top_entities = ner_data.nlargest(limit, 'frequency')
        else:
            top_entities = ner_data.head(limit)
        
        entities = top_entities.to_dict('records')
        
        return jsonify({
            "status": "success",
            "entities": entities,
            "total_entities": len(ner_data),
            "returned_count": len(entities),
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"[VIZ_SERVER] Error getting NER entities: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error retrieving NER entities: {str(e)}"
        }), 500

@app.route('/knowledge-graph', methods=['GET'])
def get_knowledge_graph():
    """Get knowledge graph data for visualization"""
    if initialization_status["status"] != "ready":
        return jsonify({
            "status": "error",
            "message": "Visualization system not ready yet",
            "initialization_status": initialization_status
        }), 503
    
    try:
        kg_data = generate_knowledge_graph_data()
        
        return jsonify({
            "status": "success",
            "graph": kg_data,
            "node_count": len(kg_data.get('nodes', [])),
            "edge_count": len(kg_data.get('edges', [])),
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"[VIZ_SERVER] Error getting knowledge graph: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error retrieving knowledge graph: {str(e)}"
        }), 500

@app.route('/embeddings', methods=['GET'])
def get_embeddings_visualization():
    """Get embeddings visualization data"""
    if initialization_status["status"] != "ready":
        return jsonify({
            "status": "error",
            "message": "Visualization system not ready yet",
            "initialization_status": initialization_status
        }), 503
    
    try:
        method = request.args.get('method', 'pca')
        
        embeddings_data = generate_embeddings_visualization(method)
        
        return jsonify({
            "status": "success",
            "embeddings": embeddings_data,
            "method": method,
            "point_count": len(embeddings_data),
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"[VIZ_SERVER] Error getting embeddings visualization: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error generating embeddings visualization: {str(e)}"
        }), 500

@app.route('/similarity', methods=['POST'])
def similarity_search():
    """Perform similarity search for visualization"""
    if initialization_status["status"] != "ready":
        return jsonify({
            "status": "error",
            "message": "Visualization system not ready yet",
            "initialization_status": initialization_status
        }), 503
    
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                "status": "error",
                "message": "Query is required"
            }), 400
        
        query = data['query']
        top_k = data.get('top_k', 10)
        
        # Simple similarity search using drug data
        if viz_data is not None and not viz_data.empty:
            results = []
            query_lower = query.lower()
            
            for idx, row in viz_data.iterrows():
                score = 0
                
                # Check similarity in drug names and conditions
                for col in ['drug_name', 'medical_condition', 'side_effects']:
                    if col in row and query_lower in str(row[col]).lower():
                        score += 1
                
                if score > 0:
                    results.append({
                        'drug_name': row.get('drug_name', 'Unknown'),
                        'medical_condition': row.get('medical_condition', 'Not specified'),
                        'similarity_score': score / 3.0,  # Normalize
                        'index': idx
                    })
            
            # Sort by similarity score
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            results = results[:top_k]
        else:
            results = []
        
        return jsonify({
            "status": "success",
            "query": query,
            "results": results,
            "total_found": len(results),
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"[VIZ_SERVER] Error in similarity search: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error in similarity search: {str(e)}"
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get detailed status information"""
    return jsonify({
        "service": "Medical Visualization Server",
        "version": "1.0.0",
        "initialization_status": initialization_status,
        "data_loaded": {
            "ner_entities": ner_data is not None,
            "visualization_data": viz_data is not None
        },
        "endpoints": {
            "health": "GET /health",
            "ner": "GET /ner?limit=100",
            "knowledge_graph": "GET /knowledge-graph",
            "embeddings": "GET /embeddings?method=pca",
            "similarity": "POST /similarity",
            "status": "GET /status"
        },
        "data_sources": {
            "ner_entities": str(Path(__file__).parent.parent / "visualizations" / "ner_entities.csv"),
            "drug_database": str(Path(__file__).parent.parent / "data" / "drugs_side_effects.csv"),
            "knowledge_graph": str(Path(__file__).parent.parent / "visualizations" / "medical_kg.graphml")
        }
    })

def main():
    """Main entry point"""
    port = int(os.getenv('VIZ_SERVER_PORT', 5003))
    
    # Start visualization system initialization in background
    init_thread = threading.Thread(target=initialize_visualization_system, daemon=True)
    init_thread.start()
    
    logger.info(f"[VIZ_SERVER] Starting visualization server on port {port}")
    logger.info(f"[VIZ_SERVER] Health check: http://localhost:{port}/health")
    logger.info(f"[VIZ_SERVER] NER endpoint: http://localhost:{port}/ner")
    logger.info(f"[VIZ_SERVER] Knowledge graph: http://localhost:{port}/knowledge-graph")
    logger.info(f"[VIZ_SERVER] Embeddings: http://localhost:{port}/embeddings")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"[VIZ_SERVER] Failed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()