// Medical AI API service - Connects to backend microservices

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001';

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
  metadata?: {
    retrieval_method: string;
    generation_method: string;
    context_used: number;
    top_k: number;
  };
  timestamp?: number;
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
  timestamp?: number;
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
  timestamp?: number;
}

// Helper function for API calls
const apiCall = async (endpoint: string, options: RequestInit = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ message: 'Network error' }));
    throw new Error(errorData.message || `HTTP ${response.status}`);
  }

  return response.json();
};

// Ask medical question using QA model
export const askMedicalQuestion = async (question: string, top_k: number = 5): Promise<QAResponse> => {
  try {
    return await apiCall('/api/qa/ask', {
      method: 'POST',
      body: JSON.stringify({ question, top_k }),
    });
  } catch (error) {
    console.error('QA API Error:', error);
    throw new Error(`Failed to get medical answer: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Get medicine recommendations based on symptoms
export const getRecommendations = async (
  symptoms: string[],
  additional_info: string = '',
  top_k: number = 5
): Promise<RecommendationResponse> => {
  try {
    return await apiCall('/api/recommend/medicines', {
      method: 'POST',
      body: JSON.stringify({ symptoms, additional_info, top_k }),
    });
  } catch (error) {
    console.error('Recommendation API Error:', error);
    throw new Error(`Failed to get recommendations: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Search medicines by query
export const searchMedicines = async (query: string, limit: number = 10): Promise<SearchResponse> => {
  try {
    return await apiCall(`/api/recommend/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  } catch (error) {
    console.error('Search API Error:', error);
    throw new Error(`Failed to search medicines: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
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

// Get NER entities for visualization
export const getNEREntities = async (limit: number = 100): Promise<NEREntity[]> => {
  try {
    const response = await apiCall(`/api/visualizations/ner?limit=${limit}`);
    return response.entities || [];
  } catch (error) {
    console.error('NER API Error:', error);
    throw new Error(`Failed to get NER entities: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Get Knowledge Graph data for visualization
export const getKnowledgeGraph = async (): Promise<KnowledgeGraphData> => {
  try {
    const response = await apiCall('/api/visualizations/knowledge-graph');
    return response.graph || { nodes: [], edges: [] };
  } catch (error) {
    console.error('Knowledge Graph API Error:', error);
    throw new Error(`Failed to get knowledge graph: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Get embedding visualization data
export const getEmbeddings = async (method: string = 'pca'): Promise<EmbeddingPoint[]> => {
  try {
    const response = await apiCall(`/api/visualizations/embeddings?method=${method}`);
    return response.embeddings || [];
  } catch (error) {
    console.error('Embeddings API Error:', error);
    throw new Error(`Failed to get embeddings: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Perform similarity search
export const performSimilaritySearch = async (query: string, top_k: number = 10) => {
  try {
    return await apiCall('/api/visualizations/similarity', {
      method: 'POST',
      body: JSON.stringify({ query, top_k }),
    });
  } catch (error) {
    console.error('Similarity Search API Error:', error);
    throw new Error(`Failed to perform similarity search: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Health check functions
export const checkSystemHealth = async () => {
  try {
    return await apiCall('/health');
  } catch (error) {
    console.error('Health Check Error:', error);
    throw error;
  }
};

export const checkQAHealth = async () => {
  try {
    return await apiCall('/api/qa/health');
  } catch (error) {
    console.error('QA Health Check Error:', error);
    throw error;
  }
};

export const checkRecommendationHealth = async () => {
  try {
    return await apiCall('/api/recommend/health');
  } catch (error) {
    console.error('Recommendation Health Check Error:', error);
    throw error;
  }
};

export const checkVisualizationHealth = async () => {
  try {
    return await apiCall('/api/visualizations/health');
  } catch (error) {
    console.error('Visualization Health Check Error:', error);
    throw error;
  }
};

// Export mock medicines for backward compatibility
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
