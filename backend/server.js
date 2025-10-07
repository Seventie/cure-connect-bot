require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const axios = require('axios');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3001;

// Model server URLs (from environment or defaults)
const QA_SERVER_URL = process.env.QA_SERVER_URL || 'http://localhost:5001';
const REC_SERVER_URL = process.env.REC_SERVER_URL || 'http://localhost:5002';
const VIZ_SERVER_URL = process.env.VIZ_SERVER_URL || 'http://localhost:5003';

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
    max: 200, // Increased limit for model requests
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

// Helper function to check model server health
async function checkModelHealth(serverUrl, serverName) {
  try {
    const response = await axios.get(`${serverUrl}/health`, { timeout: 5000 });
    return {
      status: 'healthy',
      data: response.data,
      url: serverUrl
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      error: error.message,
      url: serverUrl
    };
  }
}

// QA API Routes - Proxy to QA Server
app.post('/api/qa/ask', async (req, res) => {
  try {
    const { question, top_k = 5 } = req.body;
    
    if (!question || question.trim() === '') {
      return res.status(400).json({ error: 'Question is required' });
    }
    
    const response = await axios.post(`${QA_SERVER_URL}/ask`, {
      question,
      top_k
    }, { timeout: 30000 });
    
    res.json({
      ...response.data,
      source: 'qa_model_server',
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('[QA_PROXY] Error:', error.message);
    res.status(500).json({
      error: 'QA service temporarily unavailable',
      message: error.message,
      fallback: 'Model server may be starting up'
    });
  }
});

app.get('/api/qa/health', async (req, res) => {
  const health = await checkModelHealth(QA_SERVER_URL, 'QA Server');
  res.json({
    service: 'QA API',
    model_server: health,
    proxy_status: 'operational'
  });
});

// Recommendation API Routes - Proxy to Recommendation Server
app.post('/api/recommend/medicines', async (req, res) => {
  try {
    const { symptoms, additional_info, top_k = 5 } = req.body;
    
    if (!symptoms || !Array.isArray(symptoms) || symptoms.length === 0) {
      return res.status(400).json({ 
        error: 'Symptoms array is required',
        example: { symptoms: ["fever", "headache"], additional_info: "experiencing for 2 days" }
      });
    }
    
    const response = await axios.post(`${REC_SERVER_URL}/recommend`, {
      symptoms,
      additional_info,
      top_k
    }, { timeout: 30000 });
    
    res.json({
      ...response.data,
      source: 'recommendation_model_server',
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('[REC_PROXY] Error:', error.message);
    res.status(500).json({
      error: 'Recommendation service temporarily unavailable',
      message: error.message,
      fallback: 'Model server may be starting up'
    });
  }
});

app.get('/api/recommend/search', async (req, res) => {
  try {
    const { q, limit = 10 } = req.query;
    
    if (!q || q.trim() === '') {
      return res.status(400).json({ error: 'Search query (q) parameter is required' });
    }
    
    const response = await axios.get(`${REC_SERVER_URL}/search`, {
      params: { q, limit },
      timeout: 15000
    });
    
    res.json({
      ...response.data,
      source: 'recommendation_model_server'
    });
    
  } catch (error) {
    console.error('[REC_SEARCH_PROXY] Error:', error.message);
    res.status(500).json({
      error: 'Search service temporarily unavailable',
      message: error.message
    });
  }
});

app.get('/api/recommend/health', async (req, res) => {
  const health = await checkModelHealth(REC_SERVER_URL, 'Recommendation Server');
  res.json({
    service: 'Recommendation API',
    model_server: health,
    proxy_status: 'operational'
  });
});

// Visualization API Routes - Proxy to Visualization Server
app.get('/api/visualizations/ner', async (req, res) => {
  try {
    const { limit = 100 } = req.query;
    
    const response = await axios.get(`${VIZ_SERVER_URL}/ner`, {
      params: { limit },
      timeout: 15000
    });
    
    res.json({
      ...response.data,
      source: 'visualization_model_server'
    });
    
  } catch (error) {
    console.error('[VIZ_NER_PROXY] Error:', error.message);
    res.status(500).json({
      error: 'NER visualization service temporarily unavailable',
      message: error.message
    });
  }
});

app.get('/api/visualizations/knowledge-graph', async (req, res) => {
  try {
    const response = await axios.get(`${VIZ_SERVER_URL}/knowledge-graph`, {
      timeout: 15000
    });
    
    res.json({
      ...response.data,
      source: 'visualization_model_server'
    });
    
  } catch (error) {
    console.error('[VIZ_KG_PROXY] Error:', error.message);
    res.status(500).json({
      error: 'Knowledge graph service temporarily unavailable',
      message: error.message
    });
  }
});

app.get('/api/visualizations/embeddings', async (req, res) => {
  try {
    const { method = 'pca' } = req.query;
    
    const response = await axios.get(`${VIZ_SERVER_URL}/embeddings`, {
      params: { method },
      timeout: 30000
    });
    
    res.json({
      ...response.data,
      source: 'visualization_model_server'
    });
    
  } catch (error) {
    console.error('[VIZ_EMB_PROXY] Error:', error.message);
    res.status(500).json({
      error: 'Embeddings visualization service temporarily unavailable',
      message: error.message
    });
  }
});

app.post('/api/visualizations/similarity', async (req, res) => {
  try {
    const { query, top_k = 10 } = req.body;
    
    if (!query || query.trim() === '') {
      return res.status(400).json({ error: 'Query text is required' });
    }
    
    const response = await axios.post(`${VIZ_SERVER_URL}/similarity`, {
      query,
      top_k
    }, { timeout: 15000 });
    
    res.json({
      ...response.data,
      source: 'visualization_model_server'
    });
    
  } catch (error) {
    console.error('[VIZ_SIM_PROXY] Error:', error.message);
    res.status(500).json({
      error: 'Similarity search service temporarily unavailable',
      message: error.message
    });
  }
});

app.get('/api/visualizations/health', async (req, res) => {
  const health = await checkModelHealth(VIZ_SERVER_URL, 'Visualization Server');
  res.json({
    service: 'Visualization API',
    model_server: health,
    proxy_status: 'operational'
  });
});

// Main health check endpoint
app.get('/health', async (req, res) => {
  const [qaHealth, recHealth, vizHealth] = await Promise.all([
    checkModelHealth(QA_SERVER_URL, 'QA Server'),
    checkModelHealth(REC_SERVER_URL, 'Recommendation Server'),
    checkModelHealth(VIZ_SERVER_URL, 'Visualization Server')
  ]);
  
  const allHealthy = [qaHealth, recHealth, vizHealth].every(h => h.status === 'healthy');
  
  res.status(allHealthy ? 200 : 503).json({
    status: allHealthy ? 'OK' : 'DEGRADED',
    timestamp: new Date().toISOString(),
    env: process.env.NODE_ENV || 'development',
    port: PORT,
    version: process.env.npm_package_version || '1.0.0',
    uptime: process.uptime(),
    model_servers: {
      qa_server: qaHealth,
      recommendation_server: recHealth,
      visualization_server: vizHealth
    },
    services: {
      groq_api_configured: !!process.env.GROQ_API_KEY,
      python_available: true,
      node_version: process.version
    }
  });
});

// API documentation endpoint
app.get('/api', (req, res) => {
  res.json({
    name: 'Medical AI API Gateway',
    version: '2.0.0',
    description: 'API Gateway for medical AI model servers',
    architecture: 'Microservices with dedicated model servers',
    model_servers: {
      qa_server: QA_SERVER_URL,
      recommendation_server: REC_SERVER_URL,
      visualization_server: VIZ_SERVER_URL
    },
    endpoints: {
      health: 'GET /health - Overall system health',
      qa: {
        ask: 'POST /api/qa/ask - Ask medical questions',
        health: 'GET /api/qa/health - QA service health'
      },
      recommend: {
        medicines: 'POST /api/recommend/medicines - Get medicine recommendations',
        search: 'GET /api/recommend/search - Search medicines',
        health: 'GET /api/recommend/health - Recommendation service health'
      },
      visualizations: {
        ner: 'GET /api/visualizations/ner - NER entities data',
        knowledge_graph: 'GET /api/visualizations/knowledge-graph - Knowledge graph data',
        embeddings: 'GET /api/visualizations/embeddings - Embeddings analysis',
        similarity: 'POST /api/visualizations/similarity - Similarity search',
        health: 'GET /api/visualizations/health - Visualization service health'
      }
    },
    documentation: 'https://github.com/Seventie/cure-connect-bot/blob/main/README.md'
  });
});

// Serve static files
app.use('/data', express.static(path.join(__dirname, '../data')));
app.use('/embeddings', express.static(path.join(__dirname, '../embeddings')));
app.use('/visualizations', express.static(path.join(__dirname, '../visualizations')));

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(`[ERROR] ${new Date().toISOString()} - ${err.stack}`);
  
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
  console.log('[BACKEND] SIGTERM received. Shutting down gracefully...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('[BACKEND] SIGINT received. Shutting down gracefully...');
  process.exit(0);
});

// Start server
app.listen(PORT, () => {
  console.log('\n' + '='.repeat(60));
  console.log('🩺 MEDICAL AI BACKEND API GATEWAY');
  console.log('='.repeat(60));
  console.log(`🌐 Server URL: http://localhost:${PORT}`);
  console.log(`🔍 Health Check: http://localhost:${PORT}/health`);
  console.log(`📚 API Docs: http://localhost:${PORT}/api`);
  console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log('='.repeat(60));
  console.log('📡 Model Server Connections:');
  console.log(`   QA Server: ${QA_SERVER_URL}`);
  console.log(`   Recommendation: ${REC_SERVER_URL}`);
  console.log(`   Visualization: ${VIZ_SERVER_URL}`);
  console.log('='.repeat(60));
  console.log('🚀 Backend API Gateway ready!');
  console.log('='.repeat(60) + '\n');
});

module.exports = app;