const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const router = express.Router();

// CSV data cache for better performance
let drugsDataCache = null;
let cacheTimestamp = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

// Helper function to load and cache drug data
function loadDrugsData() {

    const csvPath = "C:\Users\abdus\Desktop\Study - AVV\SEM 5\NLP\Love\cure-connect-bot\data\drugs_side_effects.csv";
    // Remove fallback/mock data, always load from CSV
    if (!fs.existsSync(csvPath)) {
        throw new Error('Drugs CSV file not found');
    }

    if (!fs.existsSync(csvPath)) {
        console.warn('[RECOMMEND] Drugs CSV file not found, using fallback data');
        return [
            ['Paracetamol', 'Pain relief, fever', 'Nausea, liver damage (overdose)'],
            ['Ibuprofen', 'Inflammation, pain, fever', 'Stomach irritation, kidney problems'],
            ['Aspirin', 'Pain, inflammation, fever', 'Stomach bleeding, allergic reactions'],
            ['Amoxicillin', 'Bacterial infections', 'Diarrhea, nausea, rash'],
            ['Omeprazole', 'Acid reflux, ulcers', 'Headache, nausea, diarrhea']
        ];
    }

    try {
        const csvContent = fs.readFileSync(csvPath, 'utf8');
        const lines = csvContent.split('\n').slice(1); // Skip header
        const parsedData = [];

        for (let line of lines) {
            if (line.trim()) {
                const parts = line.split(',').map(part => part.trim().replace(/"/g, ''));
                if (parts.length >= 3) {
                    parsedData.push(parts);
                }
            }
            // Limit to prevent memory issues
            if (parsedData.length >= 1000) break;
        }

        drugsDataCache = parsedData;
        cacheTimestamp = Date.now();
        console.log(`[RECOMMEND] Loaded ${parsedData.length} drug records`);
        return parsedData;
    } catch (error) {
        console.error('[RECOMMEND] Error loading drugs data:', error);
        return [];
    }
}

// Helper function to execute Python model with timeout
function executePythonModel(scriptPath, args, timeoutMs = 30000) {
    return new Promise((resolve, reject) => {
        const pythonExe = process.env.PYTHON_EXECUTABLE || 'python';
        const pythonProcess = spawn(pythonExe, [scriptPath, ...args], {
            cwd: path.join(__dirname, '../..'),
            timeout: timeoutMs
        });

        let stdout = '';
        let stderr = '';
        let isResolved = false;

        // Timeout handler
        const timeoutHandler = setTimeout(() => {
            if (!isResolved) {
                pythonProcess.kill('SIGTERM');
                isResolved = true;
                reject(new Error('Python model execution timed out'));
            }
        }, timeoutMs);

        pythonProcess.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        pythonProcess.on('close', (code) => {
            if (isResolved) return;
            clearTimeout(timeoutHandler);
            isResolved = true;

            if (code === 0) {
                try {
                    const result = JSON.parse(stdout.trim());
                    resolve(result);
                } catch (parseError) {
                    resolve({ status: 'success', answer: stdout.trim() });
                }
            } else {
                reject(new Error(`Python process exited with code ${code}: ${stderr}`));
            }
        });

        pythonProcess.on('error', (error) => {
            if (isResolved) return;
            clearTimeout(timeoutHandler);
            isResolved = true;
            reject(error);
        });
    });
}

// POST /api/recommend/medicines - Get medicine recommendations
router.post('/medicines', async(req, res) => {
    try {
        const { symptoms, additional_info, top_k = 5 } = req.body;

        if (!symptoms || !Array.isArray(symptoms) || symptoms.length === 0) {
            return res.status(400).json({
                error: 'Symptoms array is required',
                example: { symptoms: ["fever", "headache"], additional_info: "experiencing for 2 days" }
            });
        }

        console.log(`[RECOMMEND] Processing symptoms: ${symptoms.join(', ')}`);
        const startTime = Date.now();

        // Try Python model first (with shorter timeout for web requests)
        let useModelResult = false;
        let modelResult = null;

        try {
            const modelPath = path.join(__dirname, '../../models/medical_v3.py');
            if (fs.existsSync(modelPath)) {
                const question = `What medicines would you recommend for these symptoms: ${symptoms.join(', ')}?`;

                modelResult = await executePythonModel(modelPath, [
                    '--symptoms', ...symptoms,
                    '--additional_info', additional_info || '',
                    '--question', question,
                    '--api'
                ], 15000); // 15 second timeout for web requests

                if (modelResult.status === 'success') {
                    useModelResult = true;
                }
            }
        } catch (modelError) {
            console.warn(`[RECOMMEND] Model execution failed: ${modelError.message}`);
        }

        // Fallback to CSV data analysis
        const drugsData = loadDrugsData();
        const recommendations = [];

        if (useModelResult && modelResult) {
            // Use model result as primary response
            const response = {
                symptoms: symptoms,
                additional_info: additional_info || '',
                recommendations: modelResult.recommendations || [],
                answer: modelResult.answer || modelResult.response,
                confidence_score: modelResult.confidence_score || 0.85,
                processing_info: {
                    method: 'ml_model',
                    model_used: 'medical_v3.py (KG + RAG + Groq)',
                    processing_time: `${Date.now() - startTime}ms`,
                    ner_entities: symptoms,
                    kg_nodes_expanded: modelResult.seed_nodes_count || 0
                },
                data_sources: ['drugs_side_effects.csv', 'medical_kg.graphml', 'corpus_embeddings.npy']
            };

            return res.json(response);
        }

        // CSV-based fallback recommendation
        const symptomMatches = new Map();

        for (let [drugName, conditions, sideEffects] of drugsData) {
            let matchScore = 0;
            let matchedSymptoms = [];

            for (let symptom of symptoms) {
                const symptomLower = symptom.toLowerCase();
                const conditionsLower = conditions.toLowerCase();

                if (conditionsLower.includes(symptomLower) ||
                    symptomLower.includes(conditionsLower.split(' ')[0])) {
                    matchScore += 1;
                    matchedSymptoms.push(symptom);
                }
            }

            if (matchScore > 0) {
                const confidence = Math.min(0.95, 0.5 + (matchScore * 0.15));

                recommendations.push({
                    drug_name: drugName,
                    condition: conditions,
                    side_effects: sideEffects,
                    matched_symptoms: matchedSymptoms,
                    confidence_score: confidence,
                    match_score: matchScore,
                    match_type: 'condition_match'
                });
            }
        }

        // Sort by match score and confidence
        recommendations.sort((a, b) => {
            if (b.match_score !== a.match_score) {
                return b.match_score - a.match_score;
            }
            return b.confidence_score - a.confidence_score;
        });

        // Add general recommendations if no specific matches
        if (recommendations.length === 0) {
            const generalRecommendations = [{
                drug_name: "Paracetamol",
                condition: "General pain relief, fever reduction",
                side_effects: "Rare: nausea, liver damage with overdose",
                matched_symptoms: symptoms.filter(s => ['pain', 'fever', 'headache'].some(term => s.toLowerCase().includes(term))),
                confidence_score: 0.70,
                match_score: 0,
                match_type: 'general_recommendation'
            }];

            recommendations.push(...generalRecommendations);
        }

        const response = {
            symptoms: symptoms,
            additional_info: additional_info || '',
            recommendations: recommendations.slice(0, parseInt(top_k)),
            total_matches: recommendations.length,
            processing_info: {
                method: 'csv_analysis',
                model_used: 'Fallback CSV analysis',
                processing_time: `${Date.now() - startTime}ms`,
                total_drugs_analyzed: drugsData.length
            },
            data_sources: ['drugs_side_effects.csv']
        };

        res.json(response);

    } catch (error) {
        console.error('[RECOMMEND] Route error:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: error.message,
            timestamp: new Date().toISOString()
        });
    }
});

// GET /api/recommend/search - Search medicines
// ...existing code...
router.get('/search', (req, res) => {
    try {
        const { q, filter_by, limit = 20 } = req.query;
        if (!q || q.trim() === '') {
            return res.status(400).json({
                error: 'Search query (q) parameter is required',
                example: '/api/recommend/search?q=paracetamol&limit=10'
            });
        }
        const startTime = Date.now();
        const drugsData = loadDrugsData(); // Always loads from CSV now

        const query = q.toLowerCase().trim();
        const searchResults = [];
        for (let [drugName, conditions, sideEffects] of drugsData) {
            const drugLower = drugName.toLowerCase();
            const conditionsLower = conditions.toLowerCase();
            const sideEffectsLower = sideEffects.toLowerCase();
            let matchScore = 0;
            let matchType = '';
            if (drugLower === query) {
                matchScore = 1.0;
                matchType = 'exact_drug_match';
            } else if (drugLower.includes(query) || query.includes(drugLower)) {
                matchScore = 0.9;
                matchType = 'drug_name_match';
            } else if (conditionsLower.includes(query)) {
                matchScore = 0.7;
                matchType = 'condition_match';
            } else if (sideEffectsLower.includes(query)) {
                matchScore = 0.5;
                matchType = 'side_effect_match';
            }
            if (matchScore > 0) {
                searchResults.push({
                    drug_name: drugName,
                    medical_condition: conditions,
                    side_effects: sideEffects,
                    match_score: matchScore,
                    match_type: matchType
                });
            }
        }
        searchResults.sort((a, b) => b.match_score - a.match_score);
        res.json({
            query: q,
            filter_by: filter_by || 'all',
            total_results: searchResults.length,
            results: searchResults.slice(0, parseInt(limit)),
            processing_info: {
                search_time: `${Date.now() - startTime}ms`,
                total_drugs_searched: drugsData.length
            },
            data_source: 'drugs_side_effects.csv'
        });
    } catch (error) {
        console.error('[SEARCH] Route error:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: error.message,
            timestamp: new Date().toISOString()
        });
    }
});
// ...existing code...

// GET /api/recommend/drug/:name - Get detailed drug information
router.get('/drug/:name', (req, res) => {
    try {
        const { name } = req.params;

        if (!name || name.trim() === '') {
            return res.status(400).json({ error: 'Drug name is required' });
        }

        const drugsData = loadDrugsData();
        const searchName = name.toLowerCase().trim();
        let drugDetails = null;

        // Find exact or close match
        for (let [drugName, conditions, sideEffects] of drugsData) {
            const drugLower = drugName.toLowerCase();

            if (drugLower === searchName || drugLower.includes(searchName) || searchName.includes(drugLower)) {
                drugDetails = {
                    drug_name: drugName,
                    generic_name: drugName,
                    brand_names: [drugName],
                    medical_conditions: conditions.split(/[;,]/).map(c => c.trim()).filter(c => c),
                    side_effects: sideEffects.split(/[;,]/).map(s => s.trim()).filter(s => s),
                    dosage_info: {
                        adult_dose: "As directed by physician",
                        max_daily_dose: "Refer to package insert or medical professional",
                        pediatric_dose: "Consult pediatrician for appropriate dosing"
                    },
                    warnings: [
                        "Take as prescribed by healthcare provider",
                        "Do not exceed recommended dose",
                        "Consult doctor if symptoms persist",
                        "Be aware of potential side effects"
                    ],
                    contraindications: [
                        "Known allergy to this medication",
                        "Severe liver or kidney dysfunction (consult doctor)",
                        "Pregnancy/breastfeeding (consult doctor)"
                    ],
                    interactions: [
                        "May interact with other medications",
                        "Inform healthcare provider of all current medications",
                        "Check with pharmacist for drug interactions"
                    ],
                    drug_class: "Refer to medical classification",
                    mechanism: "Consult pharmacology references for detailed mechanism",
                    data_source: "drugs_side_effects.csv",
                    last_updated: new Date().toISOString().split('T')[0]
                };
                break;
            }
        }

        if (!drugDetails) {
            return res.status(404).json({
                error: 'Drug not found',
                searched_for: name,
                suggestions: [
                    'Check spelling of drug name',
                    'Try searching with generic or brand name',
                    'Use the search endpoint: /api/recommend/search?q=' + encodeURIComponent(name)
                ],
                available_count: drugsData.length
            });
        }

        res.json(drugDetails);

    } catch (error) {
        console.error('[DRUG_DETAIL] Route error:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: error.message,
            timestamp: new Date().toISOString()
        });
    }
});

// GET /api/recommend/health - Health check
router.get('/health', (req, res) => {
    const csvPath = path.join(__dirname, '../../data/drugs_side_effects.csv');
    const kgPath = path.join(__dirname, '../../embeddings/kg_rag_artifacts/medical_kg.graphml');
    const embeddingsPath = path.join(__dirname, '../../embeddings/kg_rag_artifacts/corpus_embeddings.npy');
    const modelPath = path.join(__dirname, '../../models/medical_v3.py');

    const csvExists = fs.existsSync(csvPath);
    const modelExists = fs.existsSync(modelPath);

    // Get CSV stats
    let csvStats = { total_records: 0, file_size: 'unknown' };
    if (csvExists) {
        try {
            const stats = fs.statSync(csvPath);
            const drugsData = loadDrugsData();
            csvStats = {
                total_records: drugsData.length,
                file_size: `${Math.round(stats.size / 1024 / 1024 * 100) / 100} MB`,
                last_modified: stats.mtime.toISOString().split('T')[0]
            };
        } catch (error) {
            csvStats.error = error.message;
        }
    }

    res.json({
        service: 'Medicine Recommendation System',
        status: csvExists ? 'operational' : 'limited',
        timestamp: new Date().toISOString(),
        model: {
            primary: 'medical_v3.py (KG + RAG + Groq)',
            fallback: 'CSV analysis with text matching',
            python_available: modelExists
        },
        data_files: {
            drugs_csv: csvExists ? `Available (${csvStats.total_records} records)` : 'Missing',
            knowledge_graph: fs.existsSync(kgPath) ? 'Available' : 'Missing',
            embeddings: fs.existsSync(embeddingsPath) ? 'Available' : 'Missing'
        },
        csv_statistics: csvStats,
        configuration: {
            python_executable: process.env.PYTHON_EXECUTABLE || 'python',
            groq_api_configured: !!process.env.GROQ_API_KEY,
            cache_enabled: true,
            cache_duration: `${CACHE_DURATION / 1000}s`
        },
        features: [
            'Medicine recommendations by symptoms',
            'Drug search and filtering',
            'Detailed drug information lookup',
            'Side effects and contraindications',
            'Multiple search algorithms',
            'Caching for improved performance'
        ],
        endpoints: {
            recommend: 'POST /api/recommend/medicines',
            search: 'GET /api/recommend/search?q=drugname',
            drug_details: 'GET /api/recommend/drug/:name',
            health: 'GET /api/recommend/health'
        }
    });
});

// Clear cache endpoint (for development)
router.post('/clear-cache', (req, res) => {
    drugsDataCache = null;
    cacheTimestamp = null;
    res.json({ message: 'Cache cleared successfully' });
});

module.exports = router;
