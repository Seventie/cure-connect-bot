// Medical AI API service - Connects to backend API gateway

// Backend API Gateway URL (all requests go through this)
const API_BASE_URL = 'http://localhost:3001/api';

// Logging utility
const logger = {
  info: (message: string, data?: any) => {
    console.log(`[API] ${new Date().toISOString()} - ${message}`, data || '');
  },
  error: (message: string, error?: any) => {
    console.error(`[API ERROR] ${new Date().toISOString()} - ${message}`, error || '');
  },
  warn: (message: string, data?: any) => {
    console.warn(`[API WARN] ${new Date().toISOString()} - ${message}`, data || '');
  }
};

export interface Medicine {
  id: string;
  name: string;
  condition: string;
  usage: string;
  sideEffects: string[];
  dosage: string;
}

export interface QAResponse {
  status: string;
  question: string;
  answer: string;
  source: string;
  metadata?: {
    retrieval_method: string;
    generation_method: string;
    context_used: number;
    top_k: number;
  };
  timestamp?: string;
}

export interface RecommendationResponse {
  status: string;
  symptoms: string[];
  additional_info: string;
  recommendations: Array<{
    drug_name: string;
    medical_condition: string;
    side_effects: string;
    relevance_score?: number;
    recommendation_reason?: string;
  }>;
  ai_advice?: string;
  total_recommendations: number;
  source: string;
  timestamp?: string;
}

export interface SearchResponse {
  status: string;
  query: string;
  results: Array<{
    drug_name: string;
    medical_condition: string;
    side_effects: string;
    score: number;
  }>;
  total_found: number;
  source: string;
  timestamp?: string;
}

// Helper function for API calls with comprehensive logging
const apiCall = async (endpoint: string, options: RequestInit = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const startTime = Date.now();
  
  logger.info(`API Request: ${options.method || 'GET'} ${endpoint}`);
  
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    const duration = Date.now() - startTime;
    logger.info(`API Response: ${response.status} (${duration}ms)`);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ 
        error: 'Network error', 
        message: `HTTP ${response.status}` 
      }));
      logger.error(`API Error Response:`, errorData);
      throw new Error(errorData.message || errorData.error || `HTTP ${response.status}`);
    }

    const data = await response.json();
    logger.info(`API Success: Received response from ${data.source || 'backend'}`);
    return data;
  } catch (error) {
    const duration = Date.now() - startTime;
    logger.error(`API Call Failed (${duration}ms):`, error);
    throw error;
  }
};

// Ask medical question using QA model through backend
export const askMedicalQuestion = async (question: string, top_k: number = 5): Promise<QAResponse> => {
  logger.info('Asking medical question', { question, top_k });
  
  try {
    const result = await apiCall('/qa/ask', {
      method: 'POST',
      body: JSON.stringify({ question, top_k }),
    });
    
    logger.info('QA Response received', { status: result.status });
    return result;
  } catch (error) {
    logger.error('QA API Error:', error);
    throw new Error(`Failed to get medical answer: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Get medicine recommendations based on symptoms through backend
export const getRecommendations = async (
  symptoms: string[],
  additional_info: string = '',
  top_k: number = 5
): Promise<RecommendationResponse> => {
  logger.info('Getting recommendations', { symptoms, additional_info, top_k });
  
  try {
    const result = await apiCall('/recommend/medicines', {
      method: 'POST',
      body: JSON.stringify({ symptoms, additional_info, top_k }),
    });
    
    logger.info('Recommendation response received', { 
      status: result.status, 
      count: result.total_recommendations 
    });
    return result;
  } catch (error) {
    logger.error('Recommendation API Error:', error);
    throw new Error(`Failed to get recommendations: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Real-time search medicines by query through backend
export const searchMedicines = async (query: string, limit: number = 10): Promise<SearchResponse> => {
  logger.info('Searching medicines', { query, limit });
  
  try {
    const result = await apiCall(`/recommend/search?q=${encodeURIComponent(query)}&limit=${limit}`, {
      method: 'GET'
    });
    
    logger.info('Search response received', { 
      status: result.status, 
      total_found: result.total_found 
    });
    return result;
  } catch (error) {
    logger.error('Search API Error:', error);
    throw new Error(`Failed to search medicines: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Debounced search for real-time functionality
let searchTimeout: NodeJS.Timeout;
export const searchMedicinesRealTime = async (
  query: string, 
  callback: (results: SearchResponse) => void,
  delay: number = 300
) => {
  logger.info('Real-time search initiated', { query, delay });
  
  clearTimeout(searchTimeout);
  
  searchTimeout = setTimeout(async () => {
    if (query.trim().length < 2) {
      logger.warn('Search query too short, skipping', { query });
      return;
    }
    
    try {
      const results = await searchMedicines(query);
      callback(results);
      logger.info('Real-time search completed', { query, count: results.total_found });
    } catch (error) {
      logger.error('Real-time search failed', error);
      callback({
        status: 'error',
        query,
        results: [],
        total_found: 0,
        source: 'frontend-error',
        timestamp: new Date().toISOString()
      });
    }
  }, delay);
};

// Visualization interfaces
export interface NEREntity {
  entity: string;
  label: string;
  frequency?: number;
}

export interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: string;
}

export interface KnowledgeGraphEdge {
  source: string;
  target: string;
  relation: string;
}

export interface KnowledgeGraphData {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
}

export interface EmbeddingPoint {
  id: number;
  x: number;
  y: number;
  label: string;
}

// Get NER entities for visualization through backend
export const getNEREntities = async (limit: number = 100): Promise<NEREntity[]> => {
  logger.info('Getting NER entities', { limit });
  
  try {
    const response = await apiCall(`/visualizations/ner?limit=${limit}`);
    logger.info('NER entities received', { count: response.entities?.length || 0 });
    return response.entities || [];
  } catch (error) {
    logger.error('NER API Error:', error);
    throw new Error(`Failed to get NER entities: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Get Knowledge Graph data for visualization through backend
export const getKnowledgeGraph = async (): Promise<KnowledgeGraphData> => {
  logger.info('Getting knowledge graph data');
  
  try {
    const response = await apiCall('/visualizations/knowledge-graph');
    const graph = response.graph || { nodes: [], edges: [] };
    logger.info('Knowledge graph received', { 
      nodes: graph.nodes?.length || 0, 
      edges: graph.edges?.length || 0 
    });
    return graph;
  } catch (error) {
    logger.error('Knowledge Graph API Error:', error);
    throw new Error(`Failed to get knowledge graph: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Get embedding visualization data through backend
export const getEmbeddings = async (method: string = 'pca'): Promise<EmbeddingPoint[]> => {
  logger.info('Getting embeddings data', { method });
  
  try {
    const response = await apiCall(`/visualizations/embeddings?method=${method}`);
    logger.info('Embeddings received', { count: response.embeddings?.length || 0 });
    return response.embeddings || [];
  } catch (error) {
    logger.error('Embeddings API Error:', error);
    throw new Error(`Failed to get embeddings: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Perform similarity search through backend
export const performSimilaritySearch = async (query: string, top_k: number = 10) => {
  logger.info('Performing similarity search', { query, top_k });
  
  try {
    const result = await apiCall('/visualizations/similarity', {
      method: 'POST',
      body: JSON.stringify({ query, top_k }),
    });
    logger.info('Similarity search completed', { query, results: result.results?.length || 0 });
    return result;
  } catch (error) {
    logger.error('Similarity Search API Error:', error);
    throw new Error(`Failed to perform similarity search: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Health check functions - all through backend
export const checkSystemHealth = async () => {
  logger.info('Checking system health');
  
  try {
    const response = await apiCall('/health', { method: 'GET' });
    logger.info('System health check completed', { status: response.status });
    return response;
  } catch (error) {
    logger.error('System health check failed:', error);
    throw error;
  }
};

export const checkQAHealth = async () => {
  logger.info('Checking QA service health');
  
  try {
    const response = await apiCall('/qa/health');
    logger.info('QA health check completed', { status: response.proxy_status });
    return response;
  } catch (error) {
    logger.error('QA Health Check Error:', error);
    throw error;
  }
};

export const checkRecommendationHealth = async () => {
  logger.info('Checking recommendation service health');
  
  try {
    const response = await apiCall('/recommend/health');
    logger.info('Recommendation health check completed', { status: response.proxy_status });
    return response;
  } catch (error) {
    logger.error('Recommendation Health Check Error:', error);
    throw error;
  }
};

export const checkVisualizationHealth = async () => {
  logger.info('Checking visualization service health');
  
  try {
    const response = await apiCall('/visualizations/health');
    logger.info('Visualization health check completed', { status: response.proxy_status });
    return response;
  } catch (error) {
    logger.error('Visualization Health Check Error:', error);
    throw error;
  }
};

// Utility to check if backend is ready
export const waitForBackendReady = async (maxAttempts: number = 30): Promise<boolean> => {
  logger.info('Waiting for backend to be ready', { maxAttempts });
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const health = await checkSystemHealth();
      if (health.status === 'OK') {
        logger.info('Backend is ready!', { attempt });
        return true;
      }
      logger.info(`Backend not ready yet (attempt ${attempt}/${maxAttempts})`, { status: health.status });
    } catch (error) {
      logger.warn(`Backend health check failed (attempt ${attempt}/${maxAttempts})`, error);
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
  }
  
  logger.error('Backend failed to become ready', { maxAttempts });
  return false;
};

// Export mock medicines for backward compatibility and fallback
export const mockMedicines: Medicine[] = [
  {
    id: "1",
    name: "Paracetamol",
    condition: "Fever, Pain",
    usage: "Take 500mg every 4-6 hours",
    sideEffects: ["Nausea", "Rash", "Liver damage (high doses)"],
    dosage: "500mg-1000mg per dose",
  },
  {
    id: "2",
    name: "Amoxicillin",
    condition: "Bacterial Infections",
    usage: "Take 250-500mg every 8 hours",
    sideEffects: ["Diarrhea", "Nausea", "Allergic reactions"],
    dosage: "250-500mg every 8 hours",
  },
  {
    id: "3",
    name: "Ibuprofen",
    condition: "Pain, Inflammation",
    usage: "Take 200-400mg every 4-6 hours",
    sideEffects: ["Stomach upset", "Heartburn", "Dizziness"],
    dosage: "200-400mg per dose",
  },
  {
    id: "4",
    name: "Omeprazole",
    condition: "Acid Reflux, GERD",
    usage: "Take 20mg once daily before meal",
    sideEffects: ["Headache", "Diarrhea", "Abdominal pain"],
    dosage: "20-40mg daily",
  },
  {
    id: "5",
    name: "Metformin",
    condition: "Type 2 Diabetes",
    usage: "Take 500mg twice daily with meals",
    sideEffects: ["Nausea", "Diarrhea", "Metallic taste"],
    dosage: "500-2000mg daily",
  },
];