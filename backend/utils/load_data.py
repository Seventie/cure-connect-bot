#!/usr/bin/env python3
"""
Data loading utilities for medical AI models
Handles loading of embeddings, datasets, knowledge graphs, and NER artifacts
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse

# Add models directory to path for importing model modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../../models'))

try:
    import faiss
except ImportError:
    print("Warning: FAISS not installed. Some functionality may be limited.")
    faiss = None

try:
    import networkx as nx
except ImportError:
    print("Warning: NetworkX not installed. Knowledge graph functionality may be limited.")
    nx = None

def load_medquad_dataset(csv_path="data/medquad_processed.csv"):
    """
    Load and return the MedQuAD processed dataset
    """
    try:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            return {
                "status": "success",
                "data": df.to_dict('records'),
                "total_records": len(df),
                "columns": df.columns.tolist()
            }
        else:
            return {
                "status": "error",
                "message": f"Dataset file not found: {csv_path}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error loading MedQuAD dataset: {str(e)}"
        }

def load_drugs_dataset(csv_path="data/drugs_side_effects.csv"):
    """
    Load and return the drugs side effects dataset
    """
    try:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            return {
                "status": "success",
                "data": df.to_dict('records'),
                "total_records": len(df),
                "columns": df.columns.tolist(),
                "unique_drugs": df['drug_name'].nunique() if 'drug_name' in df.columns else 0,
                "unique_conditions": df['medical_condition'].nunique() if 'medical_condition' in df.columns else 0
            }
        else:
            return {
                "status": "error",
                "message": f"Dataset file not found: {csv_path}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error loading drugs dataset: {str(e)}"
        }

def load_embeddings(npy_path="embeddings/encoded_docs.npy"):
    """
    Load and analyze embeddings from numpy file
    """
    try:
        if os.path.exists(npy_path):
            embeddings = np.load(npy_path)
            return {
                "status": "success",
                "shape": embeddings.shape,
                "dtype": str(embeddings.dtype),
                "memory_usage_mb": embeddings.nbytes / (1024 * 1024),
                "mean_norm": float(np.mean(np.linalg.norm(embeddings, axis=1))),
                "std_norm": float(np.std(np.linalg.norm(embeddings, axis=1)))
            }
        else:
            return {
                "status": "error",
                "message": f"Embeddings file not found: {npy_path}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error loading embeddings: {str(e)}"
        }

def load_faiss_index(index_path="embeddings/faiss.index"):
    """
    Load and get information about FAISS index
    """
    try:
        if faiss is None:
            return {
                "status": "error",
                "message": "FAISS not installed"
            }
        
        if os.path.exists(index_path):
            index = faiss.read_index(index_path)
            return {
                "status": "success",
                "total_vectors": index.ntotal,
                "dimension": index.d,
                "index_type": type(index).__name__,
                "is_trained": index.is_trained,
                "metric_type": "Inner Product" if hasattr(index, 'metric_type') else "Unknown"
            }
        else:
            return {
                "status": "error",
                "message": f"FAISS index file not found: {index_path}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error loading FAISS index: {str(e)}"
        }

def load_knowledge_graph(graphml_path="visualizations/medical_kg.graphml"):
    """
    Load and analyze knowledge graph from GraphML file
    """
    try:
        if nx is None:
            return {
                "status": "error",
                "message": "NetworkX not installed"
            }
        
        if os.path.exists(graphml_path):
            G = nx.read_graphml(graphml_path)
            
            # Analyze node types
            node_types = {}
            for node, data in G.nodes(data=True):
                node_type = data.get('type', 'Unknown')
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            # Analyze edge types
            edge_types = {}
            for u, v, data in G.edges(data=True):
                edge_type = data.get('relation', 'Unknown')
                edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
            
            return {
                "status": "success",
                "total_nodes": G.number_of_nodes(),
                "total_edges": G.number_of_edges(),
                "is_directed": G.is_directed(),
                "node_types": node_types,
                "edge_types": edge_types,
                "avg_degree": sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0
            }
        else:
            return {
                "status": "error",
                "message": f"Knowledge graph file not found: {graphml_path}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error loading knowledge graph: {str(e)}"
        }

def load_ner_entities(csv_path="visualizations/ner_entities.csv"):
    """
    Load and analyze NER entities from CSV file
    """
    try:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            
            # Analyze entity types
            entity_type_counts = df['label'].value_counts().to_dict() if 'label' in df.columns else {}
            
            return {
                "status": "success",
                "total_entities": len(df),
                "entity_types": entity_type_counts,
                "columns": df.columns.tolist(),
                "sample_entities": df.head(10).to_dict('records') if len(df) > 0 else []
            }
        else:
            return {
                "status": "error",
                "message": f"NER entities file not found: {csv_path}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error loading NER entities: {str(e)}"
        }

def get_system_status():
    """
    Get overall system status and data availability
    """
    status = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "datasets": {
            "medquad": load_medquad_dataset(),
            "drugs_side_effects": load_drugs_dataset()
        },
        "embeddings": {
            "numpy_embeddings": load_embeddings(),
            "faiss_index": load_faiss_index()
        },
        "visualizations": {
            "knowledge_graph": load_knowledge_graph(),
            "ner_entities": load_ner_entities()
        }
    }
    
    return status

def main():
    parser = argparse.ArgumentParser(description='Load and analyze medical AI data')
    parser.add_argument('--component', choices=['all', 'datasets', 'embeddings', 'kg', 'ner'], 
                       default='all', help='Component to analyze')
    parser.add_argument('--output', choices=['json', 'summary'], default='json', 
                       help='Output format')
    
    args = parser.parse_args()
    
    if args.component == 'all':
        result = get_system_status()
    elif args.component == 'datasets':
        result = {
            "medquad": load_medquad_dataset(),
            "drugs_side_effects": load_drugs_dataset()
        }
    elif args.component == 'embeddings':
        result = {
            "numpy_embeddings": load_embeddings(),
            "faiss_index": load_faiss_index()
        }
    elif args.component == 'kg':
        result = load_knowledge_graph()
    elif args.component == 'ner':
        result = load_ner_entities()
    
    if args.output == 'json':
        print(json.dumps(result, indent=2))
    else:
        # Print summary
        print("=== Medical AI Data Loader Status ===")
        print(f"Timestamp: {pd.Timestamp.now()}\n")
        
        def print_status(data, prefix=""):
            if isinstance(data, dict):
                if 'status' in data:
                    status_icon = "✓" if data['status'] == 'success' else "✗"
                    print(f"{prefix}{status_icon} {data.get('message', 'Success')}")
                else:
                    for key, value in data.items():
                        print(f"{prefix}{key}:")
                        print_status(value, prefix + "  ")
        
        print_status(result)

if __name__ == "__main__":
    main()