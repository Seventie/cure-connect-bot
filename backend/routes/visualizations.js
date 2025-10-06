const express = require('express');
const path = require('path');
const fs = require('fs');
const router = express.Router();

// GET /api/visualizations/ner - Get NER entities data
router.get('/ner', async (req, res) => {
  try {
    const { limit = 100, entity_type } = req.query;
    
    // Placeholder NER data
    const nerData = {
      total_entities: 2847,
      entity_types: [
        { type: 'DRUG', count: 1245, color: '#4CAF50' },
        { type: 'CONDITION', count: 892, color: '#2196F3' },
        { type: 'SYMPTOM', count: 456, color: '#FF9800' },
        { type: 'DOSAGE', count: 178, color: '#9C27B0' },
        { type: 'SIDE_EFFECT', count: 76, color: '#F44336' }
      ],
      entities: [
        {
          text: "paracetamol",
          label: "DRUG",
          start_pos: 15,
          end_pos: 26,
          confidence: 0.98,
          source_doc: "drug_description_001"
        },
        {
          text: "fever",
          label: "SYMPTOM", 
          start_pos: 45,
          end_pos: 50,
          confidence: 0.95,
          source_doc: "condition_text_045"
        },
        {
          text: "hypertension",
          label: "CONDITION",
          start_pos: 78,
          end_pos: 90,
          confidence: 0.97,
          source_doc: "medical_record_123"
        }
      ].slice(0, parseInt(limit))
    };

    // Filter by entity type if specified
    if (entity_type) {
      nerData.entities = nerData.entities.filter(e => e.label === entity_type.toUpperCase());
    }

    // TODO: Load actual NER data from ner_entities.csv
    // const nerCsvPath = path.join(__dirname, '../../visualizations/ner_entities.csv');
    // if (fs.existsSync(nerCsvPath)) {
    //   // Read and parse NER CSV data
    // }

    res.json(nerData);
  } catch (error) {
    console.error('NER visualization error:', error);
    res.status(500).json({ error: 'Internal server error', message: error.message });
  }
});

// GET /api/visualizations/knowledge-graph - Get knowledge graph data
router.get('/knowledge-graph', async (req, res) => {
  try {
    const { node_limit = 50, edge_limit = 100 } = req.query;
    
    // Placeholder knowledge graph data
    const kgData = {
      summary: {
        total_nodes: 3456,
        total_edges: 8912,
        node_types: {
          'DRUG': 1234,
          'CONDITION': 987,
          'SIDE_EFFECT': 765,
          'SYMPTOM': 470
        },
        edge_types: {
          'TREATS': 2341,
          'CAUSES': 1876,
          'INTERACTS_WITH': 1543,
          'CONTRAINDICATED_FOR': 987,
          'RELATED_TO': 2165
        }
      },
      nodes: [
        {
          id: 'DRUG::paracetamol',
          label: 'Paracetamol',
          type: 'DRUG',
          properties: {
            generic_name: 'Acetaminophen',
            drug_class: 'Analgesic',
            molecular_formula: 'C8H9NO2'
          }
        },
        {
          id: 'CONDITION::fever',
          label: 'Fever',
          type: 'CONDITION',
          properties: {
            icd_code: 'R50',
            category: 'Symptom'
          }
        },
        {
          id: 'SIDE_EFFECT::nausea',
          label: 'Nausea',
          type: 'SIDE_EFFECT',
          properties: {
            severity: 'mild',
            frequency: 'common'
          }
        }
      ].slice(0, parseInt(node_limit)),
      edges: [
        {
          source: 'DRUG::paracetamol',
          target: 'CONDITION::fever',
          relation: 'TREATS',
          weight: 0.95,
          properties: {
            evidence_strength: 'high',
            clinical_trials: 23
          }
        },
        {
          source: 'DRUG::paracetamol',
          target: 'SIDE_EFFECT::nausea',
          relation: 'CAUSES',
          weight: 0.23,
          properties: {
            frequency: '2-5%',
            severity: 'mild'
          }
        }
      ].slice(0, parseInt(edge_limit))
    };

    // TODO: Load actual KG data from medical_kg.graphml
    // const kgPath = path.join(__dirname, '../../visualizations/medical_kg.graphml');
    // if (fs.existsSync(kgPath)) {
    //   // Parse GraphML file and extract nodes/edges
    // }

    res.json(kgData);
  } catch (error) {
    console.error('Knowledge graph visualization error:', error);
    res.status(500).json({ error: 'Internal server error', message: error.message });
  }
});

// GET /api/visualizations/embeddings - Get embeddings analysis data
router.get('/embeddings', async (req, res) => {
  try {
    const { sample_size = 20, dimension_analysis = false } = req.query;
    
    // Placeholder embeddings data
    const embeddingsData = {
      summary: {
        total_embeddings: 16407,
        embedding_dimension: 768,
        model_used: 'all-MiniLM-L6-v2',
        file_size: '125.3 MB',
        avg_cosine_similarity: 0.34
      },
      sample_embeddings: Array.from({ length: parseInt(sample_size) }, (_, i) => ({
        id: i,
        text: `Sample medical text ${i + 1}`,
        embedding_preview: Array.from({ length: 10 }, () => (Math.random() - 0.5) * 2),
        norm: Math.random() * 0.5 + 0.75,
        cluster_id: Math.floor(Math.random() * 8)
      })),
      clusters: [
        { id: 0, label: 'Pain Management', size: 2134, avg_similarity: 0.78 },
        { id: 1, label: 'Cardiovascular', size: 1876, avg_similarity: 0.82 },
        { id: 2, label: 'Respiratory', size: 1654, avg_similarity: 0.75 },
        { id: 3, label: 'Gastrointestinal', size: 1432, avg_similarity: 0.79 },
        { id: 4, label: 'Neurological', size: 1298, avg_similarity: 0.81 },
        { id: 5, label: 'Endocrine', size: 987, avg_similarity: 0.77 },
        { id: 6, label: 'Dermatological', size: 876, avg_similarity: 0.74 },
        { id: 7, label: 'Infectious Disease', size: 654, avg_similarity: 0.76 }
      ]
    };

    if (dimension_analysis === 'true') {
      embeddingsData.dimension_analysis = {
        variance_explained: Array.from({ length: 50 }, (_, i) => ({
          component: i + 1,
          variance: Math.exp(-i * 0.1) * 0.1
        })),
        top_dimensions: [
          { dim: 42, importance: 0.156, semantic_meaning: 'pain-related terms' },
          { dim: 127, importance: 0.143, semantic_meaning: 'drug dosages' },
          { dim: 89, importance: 0.134, semantic_meaning: 'symptoms description' }
        ]
      };
    }

    // TODO: Load actual embeddings data from encoded_docs.npy
    // const embeddingsPath = path.join(__dirname, '../../embeddings/encoded_docs.npy');
    // if (fs.existsSync(embeddingsPath)) {
    //   // Load and analyze numpy embeddings file
    // }

    res.json(embeddingsData);
  } catch (error) {
    console.error('Embeddings visualization error:', error);
    res.status(500).json({ error: 'Internal server error', message: error.message });
  }
});

// GET /api/visualizations/similarity - Perform similarity search for visualization
router.post('/similarity', async (req, res) => {
  try {
    const { query_text, top_k = 10 } = req.body;
    
    if (!query_text || query_text.trim() === '') {
      return res.status(400).json({ error: 'Query text is required' });
    }

    // Placeholder similarity results
    const similarityResults = {
      query: query_text,
      results: Array.from({ length: parseInt(top_k) }, (_, i) => ({
        id: i,
        text: `Similar medical text ${i + 1} related to: ${query_text}`,
        similarity_score: Math.random() * 0.3 + 0.7, // 0.7 to 1.0
        source: `document_${Math.floor(Math.random() * 1000)}`,
        embedding_distance: Math.random() * 0.5,
        cluster_id: Math.floor(Math.random() * 8)
      })).sort((a, b) => b.similarity_score - a.similarity_score)
    };

    // TODO: Implement actual similarity search using FAISS index
    
    res.json(similarityResults);
  } catch (error) {
    console.error('Similarity search error:', error);
    res.status(500).json({ error: 'Internal server error', message: error.message });
  }
});

// GET /api/visualizations/health - Health check for visualization service
router.get('/health', (req, res) => {
  res.json({
    service: 'Medical Visualizations',
    status: 'ready',
    features: [
      'NER entity visualization',
      'Knowledge graph exploration',
      'Embeddings analysis',
      'Similarity search visualization',
      'Cluster analysis'
    ],
    data_sources: [
      'ner_entities.csv',
      'medical_kg.graphml',
      'encoded_docs.npy',
      'faiss.index'
    ]
  });
});

module.exports = router;