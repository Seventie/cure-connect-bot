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
