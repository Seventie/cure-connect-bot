#!/usr/bin/env python3
"""
Recommendation Server - HTTP wrapper for medical_v3.py model
Provides REST API endpoints for medicine recommendations using drugs_side_effects.csv
"""

import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import re

# Add current directory to path to import medical_v3.py
sys.path.append(str(Path(__file__).parent))

try:
    from medical_v3 import answer_via_kg_and_semantics, run_api_mode
except ImportError as e:
    print(f"[ERROR] Could not import medical_v3 system: {e}")
    answer_via_kg_and_semantics = None
    run_api_mode = None

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
drugs_data = None
initialization_status = {"status": "initializing", "message": "Loading drug database..."}

def clean_text(text):
    """Clean and normalize text"""
    if pd.isna(text):
        return ""
    s = str(text)
    s = re.sub(r"[\r\n]+", " ", s)
    s = re.sub(r"[^A-Za-z0-9\s\-,\.;:()/%]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def initialize_recommendation_system():
    """Initialize the recommendation system in a separate thread"""
    global drugs_data, initialization_status
    
    try:
        logger.info("[REC_SERVER] Starting recommendation system initialization...")
        initialization_status = {"status": "initializing", "message": "Loading drug database..."}
        
        # Load drugs data from CSV file in data directory
        data_path = Path(__file__).parent.parent / "data" / "drugs_side_effects.csv"
        
        if not data_path.exists():
            raise Exception(f"Drug database not found at {data_path}")
        
        drugs_data = pd.read_csv(data_path)
        
        # Clean the data
        for col in ["drug_name", "side_effects", "medical_condition"]:
            if col in drugs_data.columns:
                drugs_data[f"{col}_clean"] = drugs_data[col].astype(str).apply(clean_text)
        
        logger.info(f"[REC_SERVER] Loaded {len(drugs_data)} drug records")
        
        initialization_status = {"status": "ready", "message": "Recommendation system ready"}
        logger.info("[REC_SERVER] Recommendation system initialized successfully")
        
    except Exception as e:
        logger.error(f"[REC_SERVER] Failed to initialize recommendation system: {e}")
        initialization_status = {
            "status": "error", 
            "message": f"Failed to initialize: {str(e)}"
        }

def search_drugs_by_keywords(query, limit=10):
    """Search drugs by keywords in name, condition, or side effects"""
    if drugs_data is None or drugs_data.empty:
        return []
    
    query_lower = query.lower()
    results = []
    
    for idx, row in drugs_data.iterrows():
        score = 0
        
        # Search in drug name
        drug_name = str(row.get('drug_name', '')).lower()
        if query_lower in drug_name:
            score += 3
        
        # Search in medical condition
        condition = str(row.get('medical_condition', '')).lower()
        if query_lower in condition:
            score += 2
        
        # Search in side effects
        side_effects = str(row.get('side_effects', '')).lower()
        if query_lower in side_effects:
            score += 1
        
        if score > 0:
            results.append({
                'drug_name': row.get('drug_name', 'Unknown'),
                'medical_condition': row.get('medical_condition', 'Not specified'),
                'side_effects': row.get('side_effects', 'Not specified'),
                'score': score
            })
    
    # Sort by score and return top results
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]

def get_recommendations_by_symptoms(symptoms, additional_info="", limit=5):
    """Get drug recommendations based on symptoms"""
    if drugs_data is None or drugs_data.empty:
        return []
    
    # Combine symptoms into search query
    search_query = " ".join(symptoms) + " " + additional_info
    
    results = []
    
    for idx, row in drugs_data.iterrows():
        score = 0
        
        # Check if symptoms match medical conditions
        condition = str(row.get('medical_condition', '')).lower()
        for symptom in symptoms:
            if symptom.lower() in condition:
                score += 2
        
        # Check additional info against drug name or condition
        if additional_info:
            drug_name = str(row.get('drug_name', '')).lower()
            if any(word.lower() in drug_name or word.lower() in condition for word in additional_info.split()):
                score += 1
        
        if score > 0:
            results.append({
                'drug_name': row.get('drug_name', 'Unknown'),
                'medical_condition': row.get('medical_condition', 'Not specified'),
                'side_effects': row.get('side_effects', 'Not specified'),
                'relevance_score': score,
                'recommendation_reason': f"Matches {score} symptom criteria"
            })
    
    # Sort by relevance score
    results.sort(key=lambda x: x['relevance_score'], reverse=True)
    return results[:limit]

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": initialization_status["status"],
        "message": initialization_status["message"],
        "service": "Recommendation Server",
        "port": int(os.getenv('REC_SERVER_PORT', 5002)),
        "drug_records": len(drugs_data) if drugs_data is not None else 0,
        "timestamp": time.time()
    })

@app.route('/search', methods=['GET'])
def search_drugs():
    """Search drugs by query"""
    if initialization_status["status"] != "ready":
        return jsonify({
            "status": "error",
            "message": "Recommendation system not ready yet",
            "initialization_status": initialization_status
        }), 503
    
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify({
                "status": "error",
                "message": "Search query (q) parameter is required"
            }), 400
        
        results = search_drugs_by_keywords(query, limit)
        
        return jsonify({
            "status": "success",
            "query": query,
            "results": results,
            "total_found": len(results),
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"[REC_SERVER] Error in drug search: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error searching drugs: {str(e)}"
        }), 500

@app.route('/recommend', methods=['POST'])
def recommend_medicines():
    """Get medicine recommendations based on symptoms"""
    if initialization_status["status"] != "ready":
        return jsonify({
            "status": "error",
            "message": "Recommendation system not ready yet",
            "initialization_status": initialization_status
        }), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "JSON body is required"
            }), 400
        
        symptoms = data.get('symptoms', [])
        additional_info = data.get('additional_info', '')
        top_k = data.get('top_k', 5)
        
        if not symptoms or not isinstance(symptoms, list):
            return jsonify({
                "status": "error",
                "message": "Symptoms array is required"
            }), 400
        
        # Get recommendations using our drug database
        recommendations = get_recommendations_by_symptoms(symptoms, additional_info, top_k)
        
        # If medical_v3 is available, also try to get AI-generated advice
        ai_advice = None
        if run_api_mode:
            try:
                question = f"What medicines or treatments are recommended for: {', '.join(symptoms)}? {additional_info}"
                ai_result = run_api_mode(symptoms, additional_info, question)
                ai_data = json.loads(ai_result)
                if ai_data.get('status') == 'success':
                    ai_advice = ai_data.get('answer')
            except Exception:
                pass  # AI advice is optional
        
        return jsonify({
            "status": "success",
            "symptoms": symptoms,
            "additional_info": additional_info,
            "recommendations": recommendations,
            "ai_advice": ai_advice,
            "total_recommendations": len(recommendations),
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"[REC_SERVER] Error in medicine recommendation: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error getting recommendations: {str(e)}"
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get detailed status information"""
    return jsonify({
        "service": "Medical Recommendation Server",
        "version": "1.0.0",
        "initialization_status": initialization_status,
        "drug_database_loaded": drugs_data is not None,
        "drug_records_count": len(drugs_data) if drugs_data is not None else 0,
        "endpoints": {
            "health": "GET /health",
            "search": "GET /search?q=query&limit=10",
            "recommend": "POST /recommend",
            "status": "GET /status"
        },
        "data_sources": {
            "drugs_database": str(Path(__file__).parent.parent / "data" / "drugs_side_effects.csv")
        }
    })

def main():
    """Main entry point"""
    port = int(os.getenv('REC_SERVER_PORT', 5002))
    
    # Start recommendation system initialization in background
    init_thread = threading.Thread(target=initialize_recommendation_system, daemon=True)
    init_thread.start()
    
    logger.info(f"[REC_SERVER] Starting recommendation server on port {port}")
    logger.info(f"[REC_SERVER] Health check: http://localhost:{port}/health")
    logger.info(f"[REC_SERVER] Search endpoint: http://localhost:{port}/search")
    logger.info(f"[REC_SERVER] Recommend endpoint: http://localhost:{port}/recommend")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"[REC_SERVER] Failed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()