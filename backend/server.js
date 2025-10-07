require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3001;

// Security Middleware
app.use(helmet({
  crossOriginEmbedderPolicy: false,
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
}));

// Performance Middleware
if (process.env.ENABLE_COMPRESSION !== 'false') {
  app.use(compression());
}

// Logging Middleware
if (process.env.ENABLE_LOGGING !== 'false') {
  app.use(morgan('combined'));
}

// Rate Limiting
if (process.env.ENABLE_RATE_LIMITING !== 'false') {
  const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // Limit each IP to 100 requests per windowMs
    message: {
      error: 'Too many requests from this IP, please try again later.',
      retryAfter: '15 minutes'
    },
    standardHeaders: true,
    legacyHeaders: false,
  });
  app.use('/api/', limiter);
}

// CORS Configuration
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:5173',
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));

// Body Parser Middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

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
  const healthData = {
    status: 'OK',
    timestamp: new Date().toISOString(),
    env: process.env.NODE_ENV || 'development',
    port: PORT,
    version: process.env.npm_package_version || '1.0.0',
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    services: {
      database: 'not_configured', // Update when DB is added
      python_models: fs.existsSync(path.join(__dirname, '../models/qa.py')) ? 'available' : 'missing',
      groq_api: process.env.GROQ_API_KEY ? 'configured' : 'not_configured'
    },
    data_files: {
      medquad: fs.existsSync(path.join(__dirname, '../data/medquad_processed.csv')) ? 'available' : 'missing',
      drugs: fs.existsSync(path.join(__dirname, '../data/drugs_side_effects.csv')) ? 'available' : 'missing',
      embeddings: fs.existsSync(path.join(__dirname, '../embeddings/encoded_docs.npy')) ? 'available' : 'missing'
    }
  };
  res.json(healthData);
});

// Serve static files for datasets and embeddings
app.use('/data', express.static(path.join(__dirname, '../data')));
app.use('/embeddings', express.static(path.join(__dirname, '../embeddings')));
app.use('/visualizations', express.static(path.join(__dirname, '../visualizations')));
app.use('/models', express.static(path.join(__dirname, '../models')));

// API Documentation endpoint
app.get('/api', (req, res) => {
  res.json({
    name: 'Medical AI API',
    version: '1.0.0',
    description: 'Backend API for medical AI question answering and drug recommendations',
    endpoints: {
      health: 'GET /health - Server health check',
      qa: {
        ask: 'POST /api/qa/ask - Ask medical questions',
        health: 'GET /api/qa/health - QA service health',
        stats: 'GET /api/qa/stats - QA model statistics'
      },
      recommend: {
        medicines: 'POST /api/recommend/medicines - Get medicine recommendations',
        search: 'GET /api/recommend/search - Search medicines',
        drug: 'GET /api/recommend/drug/:name - Get drug details',
        health: 'GET /api/recommend/health - Recommendation service health'
      },
      visualizations: {
        ner: 'GET /api/visualizations/ner - NER entities data',
        knowledge_graph: 'GET /api/visualizations/knowledge-graph - Knowledge graph data',
        embeddings: 'GET /api/visualizations/embeddings - Embeddings analysis',
        similarity: 'POST /api/visualizations/similarity - Similarity search'
      }
    },
    documentation: 'https://github.com/Seventie/cure-connect-bot/blob/main/README.md'
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(`[ERROR] ${new Date().toISOString()} - ${err.stack}`);
  
  // Don't leak error details in production
  const isDevelopment = process.env.NODE_ENV === 'development';
  
  res.status(err.status || 500).json({
    error: 'Internal server error',
    message: isDevelopment ? err.message : 'Something went wrong',
    timestamp: new Date().toISOString(),
    ...(isDevelopment && { stack: err.stack })
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Route not found',
    path: req.originalUrl,
    method: req.method,
    timestamp: new Date().toISOString(),
    available_routes: ['/health', '/api', '/api/qa', '/api/recommend', '/api/visualizations']
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received. Shutting down gracefully...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('SIGINT received. Shutting down gracefully...');
  process.exit(0);
});

// Start server
app.listen(PORT, () => {
  console.log('\n' + '='.repeat(60));
  console.log('🩺 MEDICAL AI BACKEND SERVER STARTED');
  console.log('='.repeat(60));
  console.log(`📍 Server URL: http://localhost:${PORT}`);
  console.log(`🔍 Health Check: http://localhost:${PORT}/health`);
  console.log(`📚 API Docs: http://localhost:${PORT}/api`);
  console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`🔑 Groq API: ${process.env.GROQ_API_KEY ? '✅ Configured' : '❌ Not configured'}`);
  console.log(`🐍 Python: ${process.env.PYTHON_EXECUTABLE || 'python'}`);
  console.log('='.repeat(60));
  console.log('🚀 Ready to serve medical AI requests!');
  console.log('='.repeat(60) + '\n');
});

module.exports = app;