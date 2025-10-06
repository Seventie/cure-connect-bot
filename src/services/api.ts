// Mock API service - Replace these with actual backend calls

export interface Medicine {
  id: string;
  name: string;
  condition: string;
  usage: string;
  sideEffects: string[];
  dosage: string;
}

export interface QAResponse {
  question: string;
  answer: string;
  confidence: number;
}

export interface RecommendationResponse {
  medicines: Medicine[];
  reasoning: string;
}

// Placeholder: Connect to your RAG-based medical QA model
export const askMedicalQuestion = async (question: string): Promise<QAResponse> => {
  // TODO: Replace with actual API call to your backend
  // Example: const response = await fetch('http://localhost:5000/api/qa', { ... })
  
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        question,
        answer: "This is a placeholder answer. Connect your RAG model at backend endpoint: POST /api/qa/ask",
        confidence: 0.85,
      });
    }, 1000);
  });
};

// Placeholder: Connect to your medicine recommendation model
export const getRecommendations = async (symptoms: string): Promise<RecommendationResponse> => {
  // TODO: Replace with actual API call to your backend
  // Example: const response = await fetch('http://localhost:5000/api/recommendations', { ... })
  
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        medicines: mockMedicines.slice(0, 3),
        reasoning: "Placeholder reasoning. Connect your recommendation model at: POST /api/recommendations/suggest",
      });
    }, 1000);
  });
};

// Mock medicine data - Replace with actual dataset integration
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

// Search and filter medicines
export const searchMedicines = async (
  query: string,
  filterBy?: string
): Promise<Medicine[]> => {
  // TODO: Replace with actual API call to your backend
  // Example: const response = await fetch('http://localhost:5000/api/medicines/search', { ... })
  
  return new Promise((resolve) => {
    setTimeout(() => {
      let results = mockMedicines;
      
      if (query) {
        results = results.filter(
          (med) =>
            med.name.toLowerCase().includes(query.toLowerCase()) ||
            med.condition.toLowerCase().includes(query.toLowerCase())
        );
      }
      
      resolve(results);
    }, 500);
  });
};

// Visualization interfaces
export interface NEREntity {
  text: string;
  label: string;
  start: number;
  end: number;
}

export interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: "drug" | "condition" | "side_effect";
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
  id: string;
  name: string;
  x: number;
  y: number;
  category: string;
}

// Mock NER data
const mockNEREntities: NEREntity[] = [
  { text: "Paracetamol", label: "DRUG", start: 0, end: 11 },
  { text: "fever", label: "SYMPTOM", start: 25, end: 30 },
  { text: "headache", label: "SYMPTOM", start: 35, end: 43 },
  { text: "liver damage", label: "SIDE_EFFECT", start: 60, end: 72 },
  { text: "Ibuprofen", label: "DRUG", start: 0, end: 9 },
  { text: "inflammation", label: "SYMPTOM", start: 25, end: 37 },
  { text: "stomach upset", label: "SIDE_EFFECT", start: 55, end: 68 },
];

// Mock Knowledge Graph data
const mockKnowledgeGraph: KnowledgeGraphData = {
  nodes: [
    { id: "1", label: "Paracetamol", type: "drug" },
    { id: "2", label: "Fever", type: "condition" },
    { id: "3", label: "Pain", type: "condition" },
    { id: "4", label: "Nausea", type: "side_effect" },
    { id: "5", label: "Liver damage", type: "side_effect" },
    { id: "6", label: "Ibuprofen", type: "drug" },
    { id: "7", label: "Inflammation", type: "condition" },
    { id: "8", label: "Stomach upset", type: "side_effect" },
    { id: "9", label: "Amoxicillin", type: "drug" },
    { id: "10", label: "Bacterial infection", type: "condition" },
    { id: "11", label: "Diarrhea", type: "side_effect" },
  ],
  edges: [
    { source: "1", target: "2", relation: "treats" },
    { source: "1", target: "3", relation: "treats" },
    { source: "1", target: "4", relation: "causes" },
    { source: "1", target: "5", relation: "causes" },
    { source: "6", target: "3", relation: "treats" },
    { source: "6", target: "7", relation: "treats" },
    { source: "6", target: "8", relation: "causes" },
    { source: "9", target: "10", relation: "treats" },
    { source: "9", target: "11", relation: "causes" },
  ],
};

// Mock embedding visualization data
const mockEmbeddings: EmbeddingPoint[] = [
  { id: "1", name: "Paracetamol", x: 10, y: 20, category: "Pain relievers" },
  { id: "2", name: "Ibuprofen", x: 15, y: 22, category: "Pain relievers" },
  { id: "3", name: "Aspirin", x: 12, y: 18, category: "Pain relievers" },
  { id: "4", name: "Amoxicillin", x: 50, y: 60, category: "Antibiotics" },
  { id: "5", name: "Penicillin", x: 48, y: 58, category: "Antibiotics" },
  { id: "6", name: "Metformin", x: 80, y: 30, category: "Diabetes" },
  { id: "7", name: "Insulin", x: 82, y: 28, category: "Diabetes" },
  { id: "8", name: "Omeprazole", x: 40, y: 80, category: "Acid reflux" },
];

// Get NER entities
export const getNEREntities = async (): Promise<NEREntity[]> => {
  // TODO: Replace with actual API call to your backend
  // Example: const response = await fetch('http://localhost:5000/api/visualizations/ner', { ... })
  
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockNEREntities);
    }, 500);
  });
};

// Get Knowledge Graph data
export const getKnowledgeGraph = async (): Promise<KnowledgeGraphData> => {
  // TODO: Replace with actual API call to your backend
  // Example: const response = await fetch('http://localhost:5000/api/visualizations/kg', { ... })
  
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockKnowledgeGraph);
    }, 500);
  });
};

// Get embedding visualization data
export const getEmbeddings = async (): Promise<EmbeddingPoint[]> => {
  // TODO: Replace with actual API call to your backend
  // Example: const response = await fetch('http://localhost:5000/api/visualizations/embeddings', { ... })
  
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockEmbeddings);
    }, 500);
  });
};
