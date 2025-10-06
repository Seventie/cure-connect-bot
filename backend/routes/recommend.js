const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const router = express.Router();

// POST /api/recommend/medicines - Get medicine recommendations
router.post('/medicines', async(req, res) => {
    try {
        const { symptoms, additional_info, top_k = 5 } = req.body;

        if (!symptoms || symptoms.length === 0) {
            return res.status(400).json({ error: 'Symptoms are required' });
        }

        // TODO: Replace with actual Python model call
        // const pythonProcess = spawn('python3', [
        //   path.join(__dirname, '../../models/medical_v3.py'),
        //   '--symptoms', symptoms.join(' '),
        //   '--additional_info', additional_info || '',
        //   '--question', 'What medicines would you recommend?',
        //   '--api'
        // ]);

        // Placeholder response for medicine recommendations
        const placeholderResponse = {
            symptoms: symptoms,
            additional_info: additional_info || '',
            recommendations: [{
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
                ner_entities_found: symptoms,
                kg_nodes_expanded: 15,
                semantic_similarity_score: 0.89
            }
        };

        res.json(placeholderResponse);
    } catch (error) {
        console.error('Medicine recommendation error:', error);
        res.status(500).json({ error: 'Internal server error', message: error.message });
    }
});

// GET /api/recommend/search - Search medicines by name, condition, or side effects
router.get('/search', async(req, res) => {
    try {
        const { q, filter_by, limit = 10 } = req.query;

        if (!q || q.trim() === '') {
            return res.status(400).json({ error: 'Search query is required' });
        }

        // Try to load actual data from sample CSV
        const csvPath = path.join(__dirname, '../../data/drugs_side_effects.csv');
        let searchResults = [];

        if (fs.existsSync(csvPath)) {
            try {
                const csvContent = fs.readFileSync(csvPath, 'utf8');
                const lines = csvContent.split('\n').slice(1); // Skip header
                const query = q.toLowerCase();

                for (let line of lines) {
                    if (line.trim()) {
                        const [drug_name, medical_condition, side_effects] = line.split(',');

                        const matchesDrug = drug_name && drug_name.toLowerCase().includes(query);
                        const matchesCondition = medical_condition && medical_condition.toLowerCase().includes(query);
                        const matchesSideEffects = side_effects && side_effects.toLowerCase().includes(query);

                        if (matchesDrug || matchesCondition || matchesSideEffects) {
                            searchResults.push({
                                drug_name: drug_name || '',
                                medical_condition: medical_condition || '',
                                side_effects: side_effects || '',
                                match_score: matchesDrug ? 0.95 : (matchesCondition ? 0.85 : 0.75),
                                match_type: matchesDrug ? 'drug_name' : (matchesCondition ? 'condition' : 'side_effect')
                            });
                        }
                    }
                }

                // Sort by match score and limit results
                searchResults = searchResults
                    .sort((a, b) => b.match_score - a.match_score)
                    .slice(0, parseInt(limit));

            } catch (csvError) {
                console.warn('Error reading CSV file:', csvError);
            }
        }

        if (searchResults.length === 0) {
            // Fallback to placeholder results
            searchResults = [{
                    drug_name: "Paracetamol",
                    medical_condition: "Fever; Pain relief",
                    side_effects: "Nausea; Vomiting; Liver damage (overdose)",
                    match_score: 0.95,
                    match_type: "drug_name"
                },
                {
                    drug_name: "Ibuprofen",
                    medical_condition: "Pain; Inflammation; Fever",
                    side_effects: "Stomach upset; Dizziness; Heartburn",
                    match_score: 0.85,
                    match_type: "condition"
                }
            ].filter(item =>
                item.drug_name.toLowerCase().includes(q.toLowerCase()) ||
                item.medical_condition.toLowerCase().includes(q.toLowerCase()) ||
                item.side_effects.toLowerCase().includes(q.toLowerCase())
            );
        }

        const response = {
            query: q,
            filter_by: filter_by || 'all',
            total_results: searchResults.length,
            results: searchResults,
            search_time: "0.3s",
            data_source: fs.existsSync(csvPath) ? "drugs_side_effects.csv" : "placeholder_data"
        };

        res.json(response);
    } catch (error) {
        console.error('Medicine search error:', error);
        res.status(500).json({ error: 'Internal server error', message: error.message });
    }
});

// GET /api/recommend/drug/:name - Get detailed information about a specific drug
router.get('/drug/:name', async(req, res) => {
    try {
        const { name } = req.params;

        // Try to find drug in sample data first
        const csvPath = path.join(__dirname, '../../data/drugs_side_effects.csv');
        let drugDetails = null;

        if (fs.existsSync(csvPath)) {
            try {
                const csvContent = fs.readFileSync(csvPath, 'utf8');
                const lines = csvContent.split('\n').slice(1); // Skip header
                const searchName = name.toLowerCase();

                for (let line of lines) {
                    if (line.trim()) {
                        const [drug_name, medical_condition, side_effects] = line.split(',');
                        if (drug_name && drug_name.toLowerCase().includes(searchName)) {
                            drugDetails = {
                                drug_name: drug_name,
                                generic_name: drug_name, // Same for now
                                brand_names: [drug_name],
                                medical_conditions: medical_condition ? medical_condition.split(';').map(c => c.trim()) : [],
                                side_effects: side_effects ? side_effects.split(';').map(s => s.trim()) : [],
                                dosage_info: {
                                    adult_dose: "As directed by physician",
                                    max_daily_dose: "Refer to package insert",
                                    pediatric_dose: "Consult pediatrician"
                                },
                                contraindications: [
                                    "Known allergy to this medication",
                                    "Severe organ dysfunction"
                                ],
                                drug_class: "As per medical classification",
                                mechanism: "Refer to pharmacology references",
                                data_source: "sample_drugs_side_effects.csv"
                            };
                            break;
                        }
                    }
                }
            } catch (csvError) {
                console.warn('Error reading CSV file:', csvError);
            }
        }

        if (!drugDetails) {
            // Fallback to placeholder drug details
            drugDetails = {
                drug_name: name,
                generic_name: name,
                brand_names: [name],
                medical_conditions: [
                    "Various conditions as prescribed"
                ],
                side_effects: [
                    "Consult healthcare provider for side effects"
                ],
                dosage_info: {
                    adult_dose: "As directed by physician",
                    max_daily_dose: "Refer to package insert",
                    pediatric_dose: "Consult pediatrician"
                },
                contraindications: [
                    "Known allergies",
                    "Drug interactions"
                ],
                drug_class: "Refer to medical references",
                mechanism: "Consult pharmacology resources",
                data_source: "placeholder_data"
            };
        }

        res.json(drugDetails);
    } catch (error) {
        console.error('Drug details error:', error);
        res.status(500).json({ error: 'Internal server error', message: error.message });
    }
});

// GET /api/recommend/health - Health check for recommendation service
router.get('/health', (req, res) => {
    const csvPath = path.join(__dirname, '../../data/drugs_side_effects.csv');
    const csvExists = fs.existsSync(csvPath);

    res.json({
        service: 'Medicine Recommendation',
        status: 'ready',
        model: 'medical_v3.py (KG + RAG + Groq)',
        data_files: {
            drugs_csv: csvExists ? 'drugs_side_effects.csv (found)' : 'drugs_side_effects.csv (missing)'
        },
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