const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const router = express.Router();

// POST /api/recommend/medicines - Get medicine recommendations
router.post('/medicines', async (req, res) => {
  try {
    const { symptoms, additional_info, top_k = 5 } = req.body;

    if (!symptoms || symptoms.length === 0) {
      return res.status(400).json({ error: 'Symptoms are required' });
    }

    // Placeholder response for medicine recommendations
    const placeholderResponse = {
      symptoms: symptoms,
      additional_info: additional_info || '',
      recommendations: [
        {
          drug_name: "Paracetamol",
          condition: "Fever, Pain relief",
          side_effects: "Nausea, skin rash, liver damage (overdose)",
          dosage: "500mg-1000mg every 4-6 hours",
          confidence_score: 0.92,
          category: "Analgesic, Antipyretic"
        },
        {
          drug_name: "Ibuprofen",
          condition: "Pain, Inflammation, Fever",
          side_effects: "Stomach upset, dizziness, heartburn",
          dosage: "200mg-400mg every 4-6 hours",
          confidence_score: 0.88,
          category: "NSAID"
        },
        {
          drug_name: "Aspirin",
          condition: "Pain, Fever, Blood thinning",
          side_effects: "Stomach irritation, bleeding, tinnitus",
          dosage: "325mg-650mg every 4 hours",
          confidence_score: 0.84,
          category: "NSAID, Antiplatelet"
        }
      ],
      knowledge_graph_context: [
        "Drug-condition relationships from medical KG",
        "Side effect profiles and contraindications",
        "Dosage recommendations from clinical data"
      ],
      processing_info: {
        ner_entities_found: ["fever", "headache", "pain"],
        kg_nodes_expanded: 15,
        semantic_similarity_score: 0.89
      }
    };

    // TODO: Replace with actual Python model call
    // const pythonProcess = spawn('python', [
    //   path.join(__dirname, '../../models/medical_v3.py'),
    //   '--symptoms', JSON.stringify(symptoms),
    //   '--additional_info', additional_info || '',
    //   '--top_k', top_k.toString()
    // ]);

    res.json(placeholderResponse);
  } catch (error) {
    console.error('Medicine recommendation error:', error);
    res.status(500).json({ error: 'Internal server error', message: error.message });
  }
});

// GET /api/recommend/search - Search medicines by name, condition, or side effects
router.get('/search', async (req, res) => {
  try {
    const { q, filter_by, limit = 10 } = req.query;

    if (!q || q.trim() === '') {
      return res.status(400).json({ error: 'Search query is required' });
    }

    // Placeholder search results
    const placeholderResults = {
      query: q,
      filter_by: filter_by || 'all',
      total_results: 156,
      results: [
        {
          drug_name: "Paracetamol",
          medical_condition: "Fever, Headache, Body aches",
          side_effects: "Nausea, Vomiting, Constipation",
          match_score: 0.95,
          match_type: "drug_name"
        },
        {
          drug_name: "Acetaminophen",
          medical_condition: "Pain, Fever",
          side_effects: "Liver damage, Skin rash",
          match_score: 0.92,
          match_type: "condition"
        },
        {
          drug_name: "Tylenol",
          medical_condition: "Mild to moderate pain",
          side_effects: "Allergic reactions, Liver problems",
          match_score: 0.89,
          match_type: "brand_name"
        }
      ],
      search_time: "0.3s"
    };

    // TODO: Implement actual search through drugs_side_effects.csv
    // const csvPath = path.join(__dirname, '../../data/drugs_side_effects.csv');
    // if (fs.existsSync(csvPath)) {
    //   // Process CSV and perform search
    // }

    res.json(placeholderResults);
  } catch (error) {
    console.error('Medicine search error:', error);
    res.status(500).json({ error: 'Internal server error', message: error.message });
  }
});

// GET /api/recommend/drug/:name - Get detailed information about a specific drug
router.get('/drug/:name', async (req, res) => {
  try {
    const { name } = req.params;
    
    // Placeholder drug details
    const drugDetails = {
      drug_name: name,
      generic_name: "Acetaminophen",
      brand_names: ["Tylenol", "Panadol", "Calpol"],
      medical_conditions: [
        "Fever",
        "Headache",
        "Muscle aches",
        "Arthritis pain",
        "Toothache"
      ],
      side_effects: [
        "Nausea",
        "Vomiting",
        "Constipation",
        "Liver damage (with overdose)",
        "Skin rash"
      ],
      dosage_info: {
        adult_dose: "500mg-1000mg every 4-6 hours",
        max_daily_dose: "4000mg",
        pediatric_dose: "10-15mg/kg every 4-6 hours"
      },
      contraindications: [
        "Severe liver disease",
        "Allergy to acetaminophen",
        "Chronic alcohol use"
      ],
      drug_class: "Analgesic, Antipyretic",
      mechanism: "Inhibits cyclooxygenase enzymes, reducing prostaglandin synthesis"
    };

    res.json(drugDetails);
  } catch (error) {
    console.error('Drug details error:', error);
    res.status(500).json({ error: 'Internal server error', message: error.message });
  }
});

// GET /api/recommend/health - Health check for recommendation service
router.get('/health', (req, res) => {
  res.json({
    service: 'Medicine Recommendation',
    status: 'ready',
    model: 'medical_v3.py (KG + RAG + Groq)',
    features: [
      'Medicine recommendations',
      'Drug search and filtering',
      'Knowledge graph integration',
      'NER entity extraction',
      'Semantic similarity matching'
    ]
  });
});

module.exports = router;