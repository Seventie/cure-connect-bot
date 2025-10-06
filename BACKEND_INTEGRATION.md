# Backend Integration Guide

This document explains how to connect your trained models to this frontend application.

## Project Structure

```
Frontend (Current Lovable Project)
├─ src/
│   ├─ pages/
│   │   ├─ Home.tsx                    # Landing page with project overview
│   │   ├─ MedicalQA.tsx               # RAG-based Q&A interface
│   │   ├─ MedicineSearch.tsx          # Medicine search and filtering
│   │   └─ MedicineRecommendation.tsx  # ML-based recommendations
│   ├─ components/
│   │   ├─ Navbar.tsx                  # Navigation component
│   │   └─ MedicineCard.tsx            # Medicine display component
│   └─ services/
│       └─ api.ts                      # API service layer (UPDATE HERE)

Backend (To Be Created by You)
├─ server.js                           # Express server
├─ routes/
│   ├─ qaRoutes.js                     # RAG QA endpoints
│   ├─ recommendationRoutes.js         # Recommendation endpoints
│   └─ dataRoutes.js                   # Medicine search endpoints
├─ models/
│   ├─ medical_v3.py                   # Your RAG QA model
│   └─ recommendation.py               # Your recommendation model
└─ data/
    ├─ medquad_processed.csv           # MedQuAD dataset
    └─ drugs_dataset.csv               # Drugs dataset
```

## API Endpoints to Implement

### 1. Medical Q&A (RAG Model)

**Endpoint:** `POST /api/qa/ask`

**Request:**
```json
{
  "question": "What are the symptoms of diabetes?"
}
```

**Response:**
```json
{
  "question": "What are the symptoms of diabetes?",
  "answer": "Diabetes symptoms include...",
  "confidence": 0.92
}
```

**Update in:** `src/services/api.ts` - `askMedicalQuestion()` function

---

### 2. Medicine Recommendations

**Endpoint:** `POST /api/recommendations/suggest`

**Request:**
```json
{
  "symptoms": "headache, fever, body aches"
}
```

**Response:**
```json
{
  "medicines": [
    {
      "id": "1",
      "name": "Paracetamol",
      "condition": "Fever, Pain",
      "usage": "Take 500mg every 4-6 hours",
      "sideEffects": ["Nausea", "Rash"],
      "dosage": "500mg-1000mg"
    }
  ],
  "reasoning": "Based on your symptoms..."
}
```

**Update in:** `src/services/api.ts` - `getRecommendations()` function

---

### 3. Medicine Search

**Endpoint:** `GET /api/medicines/search?query=paracetamol`

**Response:**
```json
[
  {
    "id": "1",
    "name": "Paracetamol",
    "condition": "Fever, Pain",
    "usage": "Take 500mg every 4-6 hours",
    "sideEffects": ["Nausea", "Rash"],
    "dosage": "500mg-1000mg"
  }
]
```

**Update in:** `src/services/api.ts` - `searchMedicines()` function

---

## How to Connect Your Backend

### Step 1: Create Backend Server

Create a Node.js/Express server:

```javascript
// server.js
const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors());
app.use(express.json());

// Import routes
const qaRoutes = require('./routes/qaRoutes');
const recommendationRoutes = require('./routes/recommendationRoutes');
const dataRoutes = require('./routes/dataRoutes');

// Use routes
app.use('/api/qa', qaRoutes);
app.use('/api/recommendations', recommendationRoutes);
app.use('/api/medicines', dataRoutes);

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
```

### Step 2: Connect Your Python Models

Create a Python API wrapper or use Flask/FastAPI:

```python
# Example with Flask
from flask import Flask, request, jsonify
import your_rag_model
import your_recommendation_model

app = Flask(__name__)

@app.route('/predict/qa', methods=['POST'])
def qa_prediction():
    question = request.json['question']
    result = your_rag_model.predict(question)
    return jsonify(result)

@app.route('/predict/recommend', methods=['POST'])
def recommend():
    symptoms = request.json['symptoms']
    result = your_recommendation_model.predict(symptoms)
    return jsonify(result)
```

### Step 3: Update Frontend API Service

In `src/services/api.ts`, replace the placeholder URLs:

```typescript
const API_BASE_URL = 'http://localhost:5000'; // Your backend URL

export const askMedicalQuestion = async (question: string): Promise<QAResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/qa/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  return response.json();
};
```

### Step 4: Load Your Datasets

Integrate your datasets in the backend:

```javascript
// routes/dataRoutes.js
const csv = require('csv-parser');
const fs = require('fs');

let medicinesData = [];

// Load drugs dataset on startup
fs.createReadStream('data/drugs_dataset.csv')
  .pipe(csv())
  .on('data', (row) => medicinesData.push(row))
  .on('end', () => console.log('Dataset loaded'));

router.get('/search', (req, res) => {
  const query = req.query.query?.toLowerCase();
  const results = medicinesData.filter(med => 
    med.name.toLowerCase().includes(query) ||
    med.condition.toLowerCase().includes(query)
  );
  res.json(results);
});
```

## Environment Variables

Create a `.env` file in your backend:

```
PORT=5000
MODEL_PATH=./models/medical_v3
DATASET_PATH=./data
```

## CORS Configuration

Make sure your backend allows requests from the frontend:

```javascript
app.use(cors({
  origin: 'http://localhost:5173', // Vite dev server
  credentials: true
}));
```

## Testing Your Integration

1. Start your backend server: `node server.js`
2. Start this frontend: Already running in Lovable
3. Test each feature through the UI
4. Check browser console for any API errors

## Deployment Notes

- **Frontend:** Deploy via Lovable's built-in deployment
- **Backend:** Deploy to services like Heroku, Railway, or AWS
- **Update API URLs:** Change `API_BASE_URL` in production

## Support

If you need help:
1. Check browser console for errors
2. Verify backend is running and accessible
3. Test API endpoints with Postman first
4. Ensure CORS is properly configured
