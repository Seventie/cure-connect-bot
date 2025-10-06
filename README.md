# 🩺 Medical AI Web Application

A full-stack web application for medical AI research and demonstration, featuring:

- **RAG-based Medical Question Answering** - Ask medical questions and get AI-powered answers
- **Medicine Search & Filtering** - Search drugs by conditions, side effects, and symptoms
- **Medicine Recommendation System** - Get drug recommendations based on symptoms
- **Data Visualizations** - Explore NER entities, knowledge graphs, and embeddings

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: Node.js + Express API server
- **AI Models**: Python-based ML models with FAISS indexing
- **Data**: Medical datasets, embeddings, and knowledge graphs

## 📁 Project Structure

```
cure-connect-bot/
├── backend/                    # Express API server
│   ├── server.js              # Main server file
│   ├── routes/                # API routes
│   │   ├── qa.js             # Question answering endpoints
│   │   ├── recommend.js      # Medicine recommendation
│   │   └── visualizations.js # Data visualization APIs
│   └── utils/                 # Backend utilities
├── src/                       # React frontend
│   ├── pages/                # Application pages
│   ├── components/           # Reusable components
│   └── services/             # API services
├── models/                    # Python AI models
│   ├── qa.py                 # RAG QA model
│   └── medical_v3.py         # Recommendation model
├── data/                      # Medical datasets
├── embeddings/               # Model embeddings and indexes
└── visualizations/           # Visualization data
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 16+ and npm
- **Python** 3.8+ with pip
- **Git**

### 1. Clone Repository

```bash
git clone https://github.com/Seventie/cure-connect-bot.git
cd cure-connect-bot
```

### 2. Python Environment Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

**Create `backend/.env`:**
```env
PORT=3001
NODE_ENV=development
CORS_ORIGIN=http://localhost:5173
GROQ_API_KEY=your-groq-api-key-here
PYTHON_EXECUTABLE=python
MEDQUAD_CSV=../data/sample_medquad_processed.csv
DRUGS_CSV=../data/sample_drugs_side_effects.csv
EMBEDDINGS_DIR=../embeddings
VISUALIZATIONS_DIR=../visualizations
MODELS_DIR=../models
```

### 4. Install Node Dependencies

```bash
# Frontend dependencies
npm install

# Backend dependencies
cd backend
npm install
cd ..
```

### 5. Add Your Data Files

Place your trained models and datasets in the appropriate directories:

- `data/` - Your medical datasets (CSV files)
- `embeddings/` - Model embeddings (.npy files) and FAISS indexes
- `visualizations/` - NER entities and knowledge graph files
- `models/` - Your Python AI model files

### 6. Start the Application

**Option A: Two terminals**

```bash
# Terminal 1 - Backend
cd backend
npm start

# Terminal 2 - Frontend (new terminal)
npm run dev
```

**Option B: Development mode with auto-restart**

```bash
# Terminal 1 - Backend with auto-restart
cd backend
npm run dev

# Terminal 2 - Frontend (new terminal)
npm run dev
```

### 7. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:3001
- **Health Check**: http://localhost:3001/health

## 🔧 API Endpoints

### Question Answering
- `POST /api/qa/ask` - Ask medical questions
- `GET /api/qa/health` - QA service health check
- `GET /api/qa/stats` - Model statistics

### Medicine Recommendation
- `POST /api/recommend/medicines` - Get medicine recommendations
- `GET /api/recommend/search` - Search medicines
- `GET /api/recommend/drug/:name` - Get drug details
- `GET /api/recommend/health` - Recommendation service health

### Visualizations
- `GET /api/visualizations/ner` - NER entities data
- `GET /api/visualizations/knowledge-graph` - Knowledge graph data
- `GET /api/visualizations/embeddings` - Embeddings analysis
- `POST /api/visualizations/similarity` - Similarity search

## 📊 Features

### 🏠 Home Page
- Project overview and introduction
- Dataset information (MedQuAD, Drug side effects)
- Model architecture explanations
- Professional academic presentation

### 🤖 Medical QA Bot
- Natural language medical question answering
- RAG (Retrieval-Augmented Generation) responses
- Context-aware answers using medical literature
- Source attribution and confidence scores

### 💊 Medicine Search
- Search medicines by name, condition, or side effects
- Advanced filtering and sorting options
- Detailed drug information pages
- Interactive search results

### 🎯 Medicine Recommendations
- Symptom-based medicine recommendations
- Multi-symptom analysis
- Confidence scoring and explanations
- Side effect warnings and contraindications

### 📈 Data Visualizations
- **NER Entities**: Explore named entities from medical texts
- **Knowledge Graph**: Interactive medical knowledge relationships
- **Embeddings**: Semantic similarity and clustering analysis
- **Statistics**: Model performance and dataset insights

## 🛠️ Development

### File Structure for Your Models

When adding your trained models, ensure the following file structure:

```
data/
├── medquad_processed.csv      # Your processed MedQuAD dataset
└── drugs_side_effects.csv     # Your drugs dataset

embeddings/
├── encoded_docs.npy          # Document embeddings
├── faiss.index              # FAISS similarity index
└── kg_rag_artifacts/        # Additional model artifacts

visualizations/
├── ner_entities.csv         # Named entity recognition results
└── medical_kg.graphml       # Medical knowledge graph
```

### Environment Variables

- `GROQ_API_KEY`: Your Groq API key for AI text generation
- `PORT`: Backend server port (default: 3001)
- `NODE_ENV`: Environment mode (development/production)
- `PYTHON_EXECUTABLE`: Python executable path

## 🔍 Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Kill process on port 3001
   netstat -ano | findstr :3001
   taskkill /PID <PID> /F
   ```

2. **Python module not found**:
   ```bash
   # Ensure virtual environment is activated
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **CORS errors**:
   - Check that `CORS_ORIGIN` in backend/.env matches your frontend URL
   - Ensure both servers are running

4. **Model loading errors**:
   - Verify all data files are in correct directories
   - Check file paths in backend/.env
   - Ensure Python dependencies are installed

### Health Checks

- Backend: http://localhost:3001/health
- QA Service: http://localhost:3001/api/qa/health
- Recommendations: http://localhost:3001/api/recommend/health
- Visualizations: http://localhost:3001/api/visualizations/health

## 📝 License

This project is for academic and research purposes.

## 🤝 Contributing

This is an academic project. For questions or issues, please check the troubleshooting section or review the API documentation.

---

**Ready to explore medical AI?** Start the servers and visit http://localhost:5173 to begin! 🚀