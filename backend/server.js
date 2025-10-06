const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Import route handlers
const qaRoutes = require('./routes/qa');
const recommendRoutes = require('./routes/recommend');
const visualizationRoutes = require('./routes/visualizations');

// API Routes
app.use('/api/qa', qaRoutes);
app.use('/api/recommend', recommendRoutes);
app.use('/api/visualizations', visualizationRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Serve static files for datasets and embeddings
app.use('/data', express.static(path.join(__dirname, '../data')));
app.use('/embeddings', express.static(path.join(__dirname, '../embeddings')));
app.use('/visualizations', express.static(path.join(__dirname, '../visualizations')));

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!', message: err.message });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

app.listen(PORT, () => {
  console.log(`🩺 Medical AI Backend Server running on port ${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/health`);
  console.log(`🤖 QA API: http://localhost:${PORT}/api/qa`);
  console.log(`💊 Recommendations API: http://localhost:${PORT}/api/recommend`);
  console.log(`📈 Visualizations API: http://localhost:${PORT}/api/visualizations`);
});

module.exports = app;