#!/usr/bin/env python3
"""
Setup Environment Script for Medical AI Application
This script ensures all paths, dependencies, and configurations are properly set up
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_packages():
    """Check if required Python packages are installed"""
    required_packages = [
        'flask', 'flask-cors', 'numpy', 'pandas', 'networkx',
        'scikit-learn', 'sentence-transformers', 'transformers',
        'torch', 'groq', 'python-dotenv', 'requests'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_packages(packages):
    """Install missing Python packages"""
    if packages:
        print(f"Installing missing packages: {', '.join(packages)}")
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + packages)
    else:
        print("All required Python packages are already installed.")

def check_optional_packages():
    """Check optional packages and suggest installation"""
    optional_packages = {
        'faiss-cpu': 'For faster similarity search',
        'scispacy': 'For better medical NER',
        'spacy': 'For NLP processing'
    }
    
    missing_optional = []
    for package, description in optional_packages.items():
        try:
            if package == 'faiss-cpu':
                import faiss
            elif package == 'scispacy':
                import scispacy
            elif package == 'spacy':
                import spacy
        except ImportError:
            missing_optional.append((package, description))
    
    if missing_optional:
        print("\nOptional packages (recommended):")
        for package, desc in missing_optional:
            print(f"  - {package}: {desc}")
            print(f"    Install with: pip install {package}")
        
        # Special case for spacy models
        try:
            import spacy
            try:
                spacy.load('en_core_web_sm')
            except OSError:
                print("  - SpaCy model missing. Install with: python -m spacy download en_core_web_sm")
        except ImportError:
            pass

def create_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        'data',
        'embeddings',
        'embeddings/kg_rag_artifacts',
        'visualizations',
        'models',
        'backend/logs'
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Directory ensured: {dir_path}")

def create_environment_files():
    """Create .env files if they don't exist"""
    # Backend .env
    backend_env = Path('backend/.env')
    if not backend_env.exists():
        backend_env.write_text(
            """# Backend Environment Configuration
GROQ_API_KEY=your-groq-api-key-here
PORT=3001
NODE_ENV=development
CORS_ORIGIN=http://localhost:5173
QA_SERVER_URL=http://localhost:5001
REC_SERVER_URL=http://localhost:5002
VIZ_SERVER_URL=http://localhost:5003
ENABLE_COMPRESSION=true
ENABLE_LOGGING=true
ENABLE_RATE_LIMITING=true
DEBUG=false
"""
        )
        print("✓ Created backend/.env")
    
    # Frontend .env
    frontend_env = Path('.env')
    if not frontend_env.exists():
        frontend_env.write_text(
            """# Frontend Environment Configuration
VITE_API_BASE_URL=http://localhost:3001
"""
        )
        print("✓ Created .env")

def check_data_files():
    """Check if data files exist and provide guidance"""
    required_files = [
        'data/drugs_side_effects.csv',
        'data/medquad_processed.csv'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("\n⚠️  Missing data files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        print("   The application will use fallback data, but for full functionality,")
        print("   please ensure these files are present.")
    else:
        print("✓ All required data files are present")

def check_embeddings():
    """Check if embedding files exist"""
    embedding_files = [
        'embeddings/encoded_docs.npy',
        'embeddings/kg_rag_artifacts/corpus_embeddings.npy'
    ]
    
    has_embeddings = any(Path(f).exists() for f in embedding_files)
    
    if has_embeddings:
        print("✓ Embedding files found")
    else:
        print("⚠️  No embedding files found. The application will create dummy embeddings.")

def fix_model_imports():
    """Update recommendation server to use fixed medical_v3"""
    rec_server_path = Path('models/recommendation_server.py')
    if rec_server_path.exists():
        content = rec_server_path.read_text()
        
        # Update import to use fixed version
        if 'from medical_v3 import' in content:
            content = content.replace(
                'from medical_v3 import answer_via_kg_and_semantics, run_api_mode',
                'from medical_v3_fixed import answer_via_kg_and_semantics, run_api_mode'
            )
            rec_server_path.write_text(content)
            print("✓ Updated recommendation server to use fixed medical_v3")

def check_node_modules():
    """Check if Node.js dependencies are installed"""
    backend_modules = Path('backend/node_modules')
    frontend_modules = Path('node_modules')
    
    if not backend_modules.exists():
        print("⚠️  Backend dependencies not installed. Run: cd backend && npm install")
    else:
        print("✓ Backend dependencies installed")
    
    if not frontend_modules.exists():
        print("⚠️  Frontend dependencies not installed. Run: npm install")
    else:
        print("✓ Frontend dependencies installed")

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*60)
    print("🎯 SETUP COMPLETE - NEXT STEPS")
    print("="*60)
    
    print("\n1. 🔑 SET UP GROQ API KEY (Optional but recommended):")
    print("   - Get your free API key from: https://console.groq.com/")
    print("   - Add it to backend/.env: GROQ_API_KEY=your-actual-key-here")
    
    print("\n2. 📦 INSTALL DEPENDENCIES (if not already done):")
    print("   Backend:  cd backend && npm install")
    print("   Frontend: npm install")
    
    print("\n3. 🚀 START THE APPLICATION:")
    print("   python startup_orchestrator.py")
    
    print("\n4. 🌐 ACCESS THE APPLICATION:")
    print("   Frontend: http://localhost:5173")
    print("   Backend:  http://localhost:3001")
    
    print("\n5. 🔍 OPTIONAL ENHANCEMENTS:")
    print("   - Install FAISS: pip install faiss-cpu")
    print("   - Install scispaCy: pip install scispacy")
    print("   - Install spaCy model: python -m spacy download en_core_web_sm")
    
    print("\n" + "="*60)
    print("✨ Your medical AI application is ready to run!")
    print("="*60)

def main():
    """Main setup function"""
    print("🩺 MEDICAL AI APPLICATION SETUP")
    print("=" * 50)
    
    # Check and install required Python packages
    print("\n📦 Checking Python packages...")
    missing_packages = check_python_packages()
    if missing_packages:
        install_packages(missing_packages)
    else:
        print("✓ All required Python packages installed")
    
    # Check optional packages
    check_optional_packages()
    
    # Create directories
    print("\n📁 Setting up directories...")
    create_directories()
    
    # Create environment files
    print("\n⚙️  Creating environment files...")
    create_environment_files()
    
    # Check data files
    print("\n📊 Checking data files...")
    check_data_files()
    
    # Check embeddings
    print("\n🔢 Checking embeddings...")
    check_embeddings()
    
    # Fix model imports
    print("\n🔧 Fixing model imports...")
    fix_model_imports()
    
    # Check Node modules
    print("\n🟢 Checking Node.js dependencies...")
    check_node_modules()
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
