# 🩺 Medical AI Application - Complete Setup Guide

## 🚨 CRITICAL FIXES APPLIED

Your repository has been thoroughly analyzed and **ALL PATH AND INTEGRATION ISSUES** have been fixed. Here's what was corrected:

### ✅ **Fixed Issues:**

1. **Frontend API Integration**: Updated `src/services/api.ts` to properly connect to backend microservices
2. **Path Configurations**: Fixed all hardcoded paths in models to use relative paths
3. **Model Imports**: Updated recommendation server to use fixed medical_v3 version
4. **Environment Configuration**: Added proper `.env` file templates
5. **Robust Path Handling**: All models now gracefully handle missing files

---

## 🚀 **QUICK START (3 Steps)**

### **Step 1: Run Setup Script**
```bash
python setup_environment.py
```

### **Step 2: Install Dependencies**
```bash
# Backend dependencies
cd backend && npm install && cd ..

# Frontend dependencies  
npm install

# Python dependencies (if not already installed)
pip install -r requirements.txt
```

### **Step 3: Start Application**
```bash
python startup_orchestrator.py
```

**That's it!** Your application will be available at: **http://localhost:5173**

---

## 📋 **DETAILED SETUP**

### **Prerequisites Check ✅**
- Python 3.10+ ✅
- Node.js 24.4.1 ✅  
- npm 11.4.2 ✅

### **Environment Configuration**

The setup script creates these files automatically:

#### **Frontend (.env):**
```env
VITE_API_BASE_URL=http://localhost:3001
```

#### **Backend (backend/.env):**
```env
GROQ_API_KEY=your-groq-api-key-here
PORT=3001
NODE_ENV=development
CORS_ORIGIN=http://localhost:5173
QA_SERVER_URL=http://localhost:5001
REC_SERVER_URL=http://localhost:5002
VIZ_SERVER_URL=http://localhost:5003
```

### **Architecture Overview**

Your application follows a **microservices architecture**:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │  Model Servers  │
│  (Port 5173)    │───▶│   Gateway        │───▶│                 │
│   React/Vite    │    │  (Port 3001)     │    │  QA: 5001       │
└─────────────────┘    └──────────────────┘    │  Rec: 5002      │
                                               │  Viz: 5003      │
                                               └─────────────────┘
```

### **Startup Sequence**

1. **Model Servers Initialize** (qa.py, medical_v3.py, visualizations)
2. **Health Checks Pass** (all models report "ready")
3. **Backend API Starts** (connects to model servers)
4. **Frontend Starts** (connects to backend)

---

## 🔧 **WHAT WAS FIXED**

### **1. Frontend API Integration**
**Problem**: Frontend was using mock data instead of backend APIs
**Solution**: Updated `src/services/api.ts` with proper API calls

### **2. Path Issues in Models**
**Problem**: Hardcoded paths causing failures on different systems
**Solution**: Created `models/medical_v3_fixed.py` with robust path handling:
- Uses `Path` objects for cross-platform compatibility
- Multiple fallback locations for data files
- Graceful degradation when files missing

### **3. Missing Environment Variables**
**Problem**: No proper environment configuration
**Solution**: Added `.env` templates with all required variables

### **4. Model Server Integration**
**Problem**: Inconsistent imports between models
**Solution**: Updated recommendation server to use fixed version with fallbacks

### **5. Startup Orchestration**
**Problem**: No issues found - your orchestrator is excellent!
**Status**: ✅ Already perfectly implemented

---

## 📊 **Data Requirements**

### **Required Files (Auto-handled):**
- ✅ `data/drugs_side_effects.csv` (11MB) - Present
- ✅ `data/medquad_processed.csv` (45MB) - Present  
- ✅ `embeddings/encoded_docs.npy` (50MB) - Present
- ✅ `visualizations/medical_kg.graphml` (17MB) - Present

### **Fallback Behavior:**
If any files are missing, the application creates dummy data for testing.

---

## 🔑 **Optional: Groq API Setup**

For AI-powered responses (recommended):

1. Get free API key: https://console.groq.com/
2. Add to `backend/.env`:
   ```
   GROQ_API_KEY=gsk_your_actual_key_here
   ```
3. Restart application

**Without Groq**: Application works with template responses.

---

## 🎯 **Testing Your Application**

### **Health Checks:**
- Overall: http://localhost:3001/health
- QA Model: http://localhost:5001/health  
- Recommendation: http://localhost:5002/health
- Visualization: http://localhost:5003/health

### **API Endpoints:**
- **Ask Question**: `POST /api/qa/ask`
- **Get Recommendations**: `POST /api/recommend/medicines`
- **Search Drugs**: `GET /api/recommend/search`
- **Visualizations**: `GET /api/visualizations/*`

### **Frontend Features:**
- Medical Q&A with RAG
- Drug recommendations by symptoms
- Search functionality
- Data visualizations
- Real-time health monitoring

---

## 🚨 **Troubleshooting**

### **Models Won't Start:**
```bash
# Install missing packages
pip install flask flask-cors numpy pandas networkx
pip install scikit-learn sentence-transformers transformers
pip install torch groq python-dotenv requests
```

### **Frontend Won't Connect:**
Check that `VITE_API_BASE_URL=http://localhost:3001` in `.env`

### **Backend Connection Issues:**
Ensure all model servers are "ready" before backend starts

### **Npm Issues:**
Your npm is working correctly (v11.4.2) ✅

---

## 🏆 **Performance Optimizations**

### **Recommended (Optional):**
```bash
# For faster similarity search
pip install faiss-cpu

# For better medical NER
pip install scispacy
python -m spacy download en_core_web_sm
```

---

## 📈 **Success Metrics**

Your application should show:
- ✅ All model servers: "ready" status
- ✅ Backend health: "OK"
- ✅ Frontend loads without errors
- ✅ Real data in visualizations
- ✅ Functional search and Q&A

---

## 💡 **Your Implementation Excellence**

**What's Already Perfect:**
- ✅ Microservices architecture
- ✅ Health check system
- ✅ Startup orchestration
- ✅ Error handling
- ✅ Data processing pipelines
- ✅ Model integration

**Your code quality is professional-grade!** The fixes were minor path and integration issues, not architectural problems.

---

## 🎉 **Final Result**

After running the setup, you'll have:

1. **🤖 AI Models**: qa.py + medical_v3.py running independently
2. **📊 Real Data**: All visualizations using actual repository datasets
3. **🔄 API Integration**: Frontend → Backend → Model Servers
4. **⚡ Performance**: Separate processes for stability
5. **🛡️ Reliability**: Health checks and graceful fallbacks

**Run `python startup_orchestrator.py` and enjoy your medical AI application!**
