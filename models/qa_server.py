#!/usr/bin/env python3
"""
QA Server - HTTP wrapper for qa.py model
Provides REST API endpoints for the QA functionality
"""

import os
import sys
import json
import logging
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time

# Add current directory to path to import qa.py
sys.path.append(str(Path(__file__).parent))

try:
    from qa import MedicalQASystem
except ImportError as e:
    print(f"[ERROR] Could not import QA system: {e}")
    MedicalQASystem = None

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global QA system instance
qa_system = None
initialization_status = {"status": "initializing", "message": "Loading QA system..."}

def initialize_qa_system():
    """Initialize the QA system in a separate thread"""
    global qa_system, initialization_status
    
    try:
        logger.info("[QA_SERVER] Starting QA system initialization...")
        initialization_status = {"status": "initializing", "message": "Loading models and data..."}
        
        if MedicalQASystem is None:
            raise Exception("QA system could not be imported")
        
        # Initialize with paths relative to repository root
        data_dir = Path(__file__).parent.parent / "data"
        embeddings_dir = Path(__file__).parent.parent / "embeddings"
        
        qa_system = MedicalQASystem(str(data_dir), str(embeddings_dir))
        
        initialization_status = {"status": "ready", "message": "QA system ready"}
        logger.info("[QA_SERVER] QA system initialized successfully")
        
    except Exception as e:
        logger.error(f"[QA_SERVER] Failed to initialize QA system: {e}")
        initialization_status = {
            "status": "error", 
            "message": f"Failed to initialize: {str(e)}"
        }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": initialization_status["status"],
        "message": initialization_status["message"],
        "service": "QA Server",
        "port": int(os.getenv('QA_SERVER_PORT', 5001)),
        "timestamp": time.time()
    })

@app.route('/ask', methods=['POST'])
def ask_question():
    """Ask a medical question"""
    global qa_system
    
    if initialization_status["status"] != "ready":
        return jsonify({
            "status": "error",
            "message": "QA system not ready yet",
            "initialization_status": initialization_status
        }), 503
    
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({
                "status": "error",
                "message": "Question is required"
            }), 400
        
        question = data['question']
        top_k = data.get('top_k', 5)
        
        if not question.strip():
            return jsonify({
                "status": "error",
                "message": "Question cannot be empty"
            }), 400
        
        # Process question using QA system
        result = qa_system.ask_question(question, top_k)
        
        return jsonify({
            "status": "success",
            "question": question,
            "answer": result.get("answer", "No answer available"),
            "metadata": {
                "retrieval_method": result.get("retrieval_method", "unknown"),
                "generation_method": result.get("generation_method", "unknown"),
                "context_used": result.get("context_used", 0),
                "top_k": top_k
            },
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"[QA_SERVER] Error processing question: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error processing question: {str(e)}"
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get detailed status information"""
    return jsonify({
        "service": "Medical QA Server",
        "version": "1.0.0",
        "initialization_status": initialization_status,
        "qa_system_loaded": qa_system is not None,
        "endpoints": {
            "health": "GET /health",
            "ask": "POST /ask",
            "status": "GET /status"
        },
        "data_sources": {
            "data_dir": str(Path(__file__).parent.parent / "data"),
            "embeddings_dir": str(Path(__file__).parent.parent / "embeddings")
        }
    })

def main():
    """Main entry point"""
    port = int(os.getenv('QA_SERVER_PORT', 5001))
    
    # Start QA system initialization in background
    init_thread = threading.Thread(target=initialize_qa_system, daemon=True)
    init_thread.start()
    
    logger.info(f"[QA_SERVER] Starting QA server on port {port}")
    logger.info(f"[QA_SERVER] Health check: http://localhost:{port}/health")
    logger.info(f"[QA_SERVER] QA endpoint: http://localhost:{port}/ask")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"[QA_SERVER] Failed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()