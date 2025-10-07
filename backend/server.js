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
const winston = require('winston');

const app = express();
const PORT = process.env.PORT || 3001;

// Enhanced Logging Configuration
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.printf(({ timestamp, level, message, stack, ...meta }) => {
      let log = `${timestamp} [${level.toUpperCase()}] ${message}`;
      if (Object.keys(meta).length > 0) {
        log += ` ${JSON.stringify(meta)}`;
      }
      if (stack) {
        log += `\n${stack}`;
      }
      return log;
    })
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'backend.log' }),
    new winston.transports.File({ filename: 'error.log', level: 'error' })
  ]
});

// Model server URLs (from environment or defaults)
const QA_SERVER_URL = process.env.QA_SERVER_URL || 'http://localhost:5001';
const REC_SERVER_URL = process.env.REC_SERVER_URL || 'http://localhost:5002';
const VIZ_SERVER_URL = process.env.VIZ_SERVER_URL || 'http://localhost:5003';

logger.info('Backend API Gateway starting up', {
  qa_server: QA_SERVER_URL,
  rec_server: REC_SERVER_URL,
  viz_server: VIZ_SERVER_URL,
  port: PORT,
  node_env: process.env.NODE_ENV || 'development'
});

// Custom request logging middleware
const requestLogger = (req, res, next) => {
  const startTime = Date.now();
  const originalJson = res.json;
  
  res.json = function(data) {
    const duration = Date.now() - startTime;
    logger.info('API Request Completed', {
      method: req.method,
      url: req.originalUrl,
      status: res.statusCode,
      duration: `${duration}ms`,
      ip: req.ip,
      userAgent: req.get('User-Agent')
    });
    return originalJson.call(this, data);
  };
  
  logger.info('API Request Started', {
    method: req.method,
    url: req.originalUrl,
    ip: req.ip
  });
  
  next();
};

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
  logger.info('Compression middleware enabled');
}

// Logging Middleware
if (process.env.ENABLE_LOGGING !== 'false') {
  app.use(morgan('combined', {
    stream: {
      write: (message) => logger.info(message.trim())
    }
  }));
}

// Custom request logging
app.use(requestLogger);

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
  logger.info('Rate limiting enabled: 200 requests per 15 minutes');
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

// Helper function to check model server health with enhanced logging
async function checkModelHealth(serverUrl, serverName) {
  const startTime = Date.now();
  
  try {
    logger.info(`Checking ${serverName} health`, { url: serverUrl });
    
    const response = await axios.get(`${serverUrl}/health`, { timeout: 10000 });
    const duration = Date.now() - startTime;
    
    logger.info(`${serverName} health check successful`, {
      url: serverUrl,
      status: response.data.status,
      duration: `${duration}ms`
    });
    
    return {
      status: 'healthy',
      data: response.data,
      url: serverUrl,
      responseTime: duration
    };
  } catch (error) {
    const duration = Date.now() - startTime;
    
    logger.error(`${serverName} health check failed`, {
      url: serverUrl,
      error: error.message,
      duration: `${duration}ms`,
      code: error.code
    });
    
    return {
      status: 'unhealthy',
      error: error.message,
      url: serverUrl,
      responseTime: duration
    };
  }
}

// Enhanced proxy function with comprehensive logging
async function proxyToModelServer(serverUrl, endpoint, options, serviceName) {
  const startTime = Date.now();
  const requestId = Math.random().toString(36).substr(2, 9);
  
  logger.info(`Proxying request to ${serviceName}`, {
    requestId,
    url: `${serverUrl}${endpoint}`,
    method: options.method || 'GET'
  });
  
  try {
    const response = await axios({
      url: `${serverUrl}${endpoint}`,
      timeout: 60000, // 60 second timeout
      ...options
    });
    
    const duration = Date.now() - startTime;
    
    logger.info(`${serviceName} proxy success`, {
      requestId,
      status: response.status,
      duration: `${duration}ms`
    });
    
    return {
      success: true,
      data: {
        ...response.data,
        source: `${serviceName.toLowerCase()}_model_server`,
        timestamp: new Date().toISOString(),
        requestId
      }
    };
    
  } catch (error) {
    const duration = Date.now() - startTime;
    
    logger.error(`${serviceName} proxy error`, {
      requestId,
      error: error.message,
      duration: `${duration}ms`,
      code: error.code,
      status: error.response?.status
    });
    
    return {
      success: false,
      error: {
        message: error.message,
        service: serviceName,
        fallback: 'Model server may be starting up or temporarily unavailable',
        requestId
      }
    };
  }
}

// QA API Routes - Enhanced with logging
app.post('/api/qa/ask', async (req, res) => {
  const { question, top_k = 5 } = req.body;
  
  logger.info('QA request received', {
    question: question?.substring(0, 100) + (question?.length > 100 ? '...' : ''),
    top_k
  });
  
  if (!question || question.trim() === '') {
    logger.warn('QA request rejected: empty question');
    return res.status(400).json({ 
      error: 'Question is required',
      timestamp: new Date().toISOString()
    });
  }
  
  const result = await proxyToModelServer(
    QA_SERVER_URL, 
    '/ask', 
    {
      method: 'POST',
      data: { question, top_k }
    },
    'QA'
  );
  
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(500).json({
      error: 'QA service temporarily unavailable',
      ...result.error
    });
  }
});

app.get('/api/qa/health', async (req, res) => {
  const health = await checkModelHealth(QA_SERVER_URL, 'QA Server');
  res.json({
    service: 'QA API',
    model_server: health,
    proxy_status: 'operational',
    timestamp: new Date().toISOString()
  });
});

// Recommendation API Routes - Enhanced with logging
app.post('/api/recommend/medicines', async (req, res) => {
  const { symptoms, additional_info, top_k = 5 } = req.body;
  
  logger.info('Recommendation request received', {
    symptoms: symptoms?.length || 0,
    additional_info: additional_info?.substring(0, 100),
    top_k
  });
  
  if (!symptoms || !Array.isArray(symptoms) || symptoms.length === 0) {
    logger.warn('Recommendation request rejected: invalid symptoms');
    return res.status(400).json({ 
      error: 'Symptoms array is required',
      example: { symptoms: ["fever", "headache"], additional_info: "experiencing for 2 days" },
      timestamp: new Date().toISOString()
    });
  }
  
  const result = await proxyToModelServer(
    REC_SERVER_URL,
    '/recommend',
    {
      method: 'POST',
      data: { symptoms, additional_info, top_k }
    },
    'Recommendation'
  );
  
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(500).json({
      error: 'Recommendation service temporarily unavailable',
      ...result.error
    });
  }
});

// Enhanced real-time search with logging
app.get('/api/recommend/search', async (req, res) => {
  const { q, limit = 10 } = req.query;
  
  logger.info('Search request received', {
    query: q?.substring(0, 50),
    limit
  });
  
  if (!q || q.trim() === '') {
    logger.warn('Search request rejected: empty query');
    return res.status(400).json({ 
      error: 'Search query (q) parameter is required',
      timestamp: new Date().toISOString()
    });
  }
  
  const result = await proxyToModelServer(
    REC_SERVER_URL,
    `/search?q=${encodeURIComponent(q)}&limit=${limit}`,
    { method: 'GET' },
    'Search'
  );
  
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(500).json({
      error: 'Search service temporarily unavailable',
      ...result.error
    });
  }
});

app.get('/api/recommend/health', async (req, res) => {
  const health = await checkModelHealth(REC_SERVER_URL, 'Recommendation Server');
  res.json({
    service: 'Recommendation API',
    model_server: health,
    proxy_status: 'operational',
    timestamp: new Date().toISOString()
  });
});

// Visualization API Routes - Enhanced with logging
app.get('/api/visualizations/ner', async (req, res) => {
  const { limit = 100 } = req.query;
  
  logger.info('NER visualization request received', { limit });
  
  const result = await proxyToModelServer(
    VIZ_SERVER_URL,
    `/ner?limit=${limit}`,
    { method: 'GET' },
    'NER Visualization'
  );
  
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(500).json({
      error: 'NER visualization service temporarily unavailable',
      ...result.error
    });
  }
});

app.get('/api/visualizations/knowledge-graph', async (req, res) => {
  logger.info('Knowledge graph request received');
  
  const result = await proxyToModelServer(
    VIZ_SERVER_URL,
    '/knowledge-graph',
    { method: 'GET' },
    'Knowledge Graph'
  );
  
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(500).json({
      error: 'Knowledge graph service temporarily unavailable',
      ...result.error
    });
  }
});

app.get('/api/visualizations/embeddings', async (req, res) => {
  const { method = 'pca' } = req.query;
  
  logger.info('Embeddings visualization request received', { method });
  
  const result = await proxyToModelServer(
    VIZ_SERVER_URL,
    `/embeddings?method=${method}`,
    { method: 'GET' },
    'Embeddings Visualization'
  );
  
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(500).json({
      error: 'Embeddings visualization service temporarily unavailable',
      ...result.error
    });
  }
});

app.post('/api/visualizations/similarity', async (req, res) => {
  const { query, top_k = 10 } = req.body;
  
  logger.info('Similarity search request received', {
    query: query?.substring(0, 50),
    top_k
  });
  
  if (!query || query.trim() === '') {
    logger.warn('Similarity search rejected: empty query');
    return res.status(400).json({ 
      error: 'Query text is required',
      timestamp: new Date().toISOString()
    });
  }
  
  const result = await proxyToModelServer(
    VIZ_SERVER_URL,
    '/similarity',
    {
      method: 'POST',
      data: { query, top_k }
    },
    'Similarity Search'
  );
  
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(500).json({
      error: 'Similarity search service temporarily unavailable',
      ...result.error
    });
  }
});

app.get('/api/visualizations/health', async (req, res) => {
  const health = await checkModelHealth(VIZ_SERVER_URL, 'Visualization Server');
  res.json({
    service: 'Visualization API',
    model_server: health,
    proxy_status: 'operational',
    timestamp: new Date().toISOString()
  });
});

// Enhanced main health check endpoint
app.get('/health', async (req, res) => {
  logger.info('System health check requested');
  
  const [qaHealth, recHealth, vizHealth] = await Promise.all([
    checkModelHealth(QA_SERVER_URL, 'QA Server'),
    checkModelHealth(REC_SERVER_URL, 'Recommendation Server'),
    checkModelHealth(VIZ_SERVER_URL, 'Visualization Server')
  ]);
  
  const allHealthy = [qaHealth, recHealth, vizHealth].every(h => h.status === 'healthy');
  
  const healthStatus = {
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
      node_version: process.version,
      logging_enabled: true
    },
    performance: {
      memory_usage: process.memoryUsage(),
      cpu_usage: process.cpuUsage()
    }
  };
  
  logger.info('System health check completed', {
    status: healthStatus.status,
    healthy_servers: [qaHealth, recHealth, vizHealth].filter(h => h.status === 'healthy').length
  });
  
  res.status(allHealthy ? 200 : 503).json(healthStatus);
});

// Enhanced API documentation endpoint
app.get('/api', (req, res) => {
  logger.info('API documentation requested');
  
  res.json({
    name: 'Medical AI API Gateway',
    version: '2.1.0',
    description: 'Enhanced API Gateway for medical AI model servers with comprehensive logging',
    architecture: 'Microservices with dedicated model servers',
    features: [
      'Real-time search with debouncing',
      'Comprehensive request/response logging',
      'Enhanced error handling and recovery',
      'Performance monitoring',
      'Health monitoring for all services'
    ],
    model_servers: {
      qa_server: QA_SERVER_URL,
      recommendation_server: REC_SERVER_URL,
      visualization_server: VIZ_SERVER_URL
    },
    endpoints: {
      health: 'GET /health - Overall system health with performance metrics',
      qa: {
        ask: 'POST /api/qa/ask - Ask medical questions',
        health: 'GET /api/qa/health - QA service health'
      },
      recommend: {
        medicines: 'POST /api/recommend/medicines - Get medicine recommendations',
        search: 'GET /api/recommend/search - Real-time medicine search',
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
    logging: {
      enabled: true,
      level: process.env.LOG_LEVEL || 'info',
      files: ['backend.log', 'error.log']
    },
    documentation: 'https://github.com/Seventie/cure-connect-bot/blob/main/README.md'
  });
});

// Serve static files
app.use('/data', express.static(path.join(__dirname, '../data')));
app.use('/embeddings', express.static(path.join(__dirname, '../embeddings')));
app.use('/visualizations', express.static(path.join(__dirname, '../visualizations')));

// Enhanced error handling middleware
app.use((err, req, res, next) => {
  const errorId = Math.random().toString(36).substr(2, 9);
  
  logger.error('Unhandled error occurred', {
    errorId,
    error: err.message,
    stack: err.stack,
    url: req.originalUrl,
    method: req.method,
    ip: req.ip
  });
  
  const isDevelopment = process.env.NODE_ENV === 'development';
  
  res.status(err.status || 500).json({
    error: 'Internal server error',
    message: isDevelopment ? err.message : 'Something went wrong',
    errorId,
    timestamp: new Date().toISOString(),
    ...(isDevelopment && { stack: err.stack })
  });
});

// Enhanced 404 handler
app.use('*', (req, res) => {
  logger.warn('Route not found', {
    url: req.originalUrl,
    method: req.method,
    ip: req.ip
  });
  
  res.status(404).json({
    error: 'Route not found',
    path: req.originalUrl,
    method: req.method,
    timestamp: new Date().toISOString(),
    available_routes: [
      '/health',
      '/api',
      '/api/qa/*',
      '/api/recommend/*',
      '/api/visualizations/*'
    ],
    documentation: 'GET /api for complete API documentation'
  });
});

// Graceful shutdown with cleanup
process.on('SIGTERM', () => {
  logger.info('SIGTERM received. Shutting down gracefully...');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received. Shutting down gracefully...');
  process.exit(0);
});

// Handle uncaught exceptions
process.on('uncaughtException', (err) => {
  logger.error('Uncaught Exception:', err);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection at Promise:', { reason, promise });
});

// Start server with enhanced logging
const server = app.listen(PORT, () => {
  console.log('\n' + '='.repeat(80));
  console.log('🩺 ENHANCED MEDICAL AI BACKEND API GATEWAY');
  console.log('='.repeat(80));
  console.log(`🌐 Server URL: http://localhost:${PORT}`);
  console.log(`🔍 Health Check: http://localhost:${PORT}/health`);
  console.log(`📚 API Docs: http://localhost:${PORT}/api`);
  console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`📄 Logging: Enabled (Level: ${process.env.LOG_LEVEL || 'info'})`);
  console.log('='.repeat(80));
  console.log('📊 Model Server Connections:');
  console.log(`   QA Server: ${QA_SERVER_URL}`);
  console.log(`   Recommendation: ${REC_SERVER_URL}`);
  console.log(`   Visualization: ${VIZ_SERVER_URL}`);
  console.log('='.repeat(80));
  console.log('🚀 Enhanced Backend API Gateway ready!');
  console.log('   • Real-time search enabled');
  console.log('   • Comprehensive logging active');
  console.log('   • Performance monitoring enabled');
  console.log('   • Enhanced error handling active');
  console.log('='.repeat(80) + '\n');
  
  logger.info('Backend server started successfully', {
    port: PORT,
    env: process.env.NODE_ENV || 'development',
    pid: process.pid,
    uptime: process.uptime()
  });
});

// Handle server startup errors
server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    logger.error(`Port ${PORT} is already in use. Please use a different port or stop the existing service.`);
  } else {
    logger.error('Server startup error:', err);
  }
  process.exit(1);
});

module.exports = app;