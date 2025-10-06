# Embeddings Directory

This directory contains precomputed embeddings and FAISS indexes for the medical AI models.

## Expected Files

### For QA Model (qa.py)
- `encoded_docs.npy` - Precomputed document embeddings from MedQuAD dataset
- `faiss.index` - FAISS index for fast similarity search

### For Recommendation Model (medical_v3.py)
- `corpus_embeddings.npy` - Sentence transformer embeddings for drug dataset
- `kg_rag_artifacts/faiss.index` - FAISS index for semantic retrieval

## File Structure
```
embeddings/
├── encoded_docs.npy          # QA model embeddings (768-dim vectors)
├── faiss.index              # QA model FAISS index
└── kg_rag_artifacts/
    ├── corpus_embeddings.npy # Recommendation model embeddings
    ├── faiss.index          # Recommendation model FAISS index
    ├── medical_kg.graphml   # Knowledge graph file
    ├── ner_entities.csv     # Named entity recognition results
    └── tfidf_vectorizer.npz # TF-IDF vectorizer (if used)
```

## Generating Embeddings

To generate these files:
1. Run your preprocessing scripts to create embeddings from the datasets
2. Build FAISS indexes for fast retrieval
3. Place files in the appropriate directories as shown above

## Notes
- Embeddings are typically 768-dimensional vectors from models like all-MiniLM-L6-v2
- FAISS indexes should be built with IndexFlatIP for inner product similarity
- File sizes can be large (100MB+) so consider using Git LFS for version control