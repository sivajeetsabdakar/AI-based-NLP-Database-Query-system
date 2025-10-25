/**
 * API Service
 * Comprehensive API integration for the NLP Query Engine
 */
import axios from 'axios';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_TIMEOUT = 30000; // 30 seconds

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging and authentication
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    
    // Handle different error types
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;
      console.error(`API Error ${status}:`, data);
      
      // Return structured error
      return Promise.reject({
        type: 'api_error',
        status,
        message: data?.error || data?.message || 'API request failed',
        details: data?.details || null,
        code: data?.code || 'UNKNOWN_ERROR'
      });
    } else if (error.request) {
      // Network error
      console.error('Network Error:', error.request);
      return Promise.reject({
        type: 'network_error',
        message: 'Network connection failed',
        code: 'NETWORK_ERROR'
      });
    } else {
      // Other error
      console.error('Request Error:', error.message);
      return Promise.reject({
        type: 'request_error',
        message: error.message,
        code: 'REQUEST_ERROR'
      });
    }
  }
);

// API Service Class
class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Health Check
  async getHealth() {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Database Connection APIs
  async connectDatabase(connectionData) {
    try {
      const response = await api.post('/api/ingest/database', connectionData);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async testDatabaseConnection(connectionString) {
    try {
      const response = await api.post('/api/ingest/database', {
        database_url: connectionString,
        test_connection: true
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Document Upload APIs
  async uploadDocuments(files, userSessionId = null, docType = null) {
    try {
      const formData = new FormData();
      
      // Add files to form data
      files.forEach((file, index) => {
        formData.append('files', file);
      });
      
      // Add optional parameters
      if (userSessionId) {
        formData.append('user_session_id', userSessionId);
      }
      if (docType) {
        formData.append('doc_type', docType);
      }

      const response = await api.post('/api/ingest/documents', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async batchUploadDocuments(files, userSessionId = null) {
    try {
      const formData = new FormData();
      
      // Add files to form data
      files.forEach((file, index) => {
        formData.append('files', file);
      });
      
      // Add optional parameters
      if (userSessionId) {
        formData.append('user_session_id', userSessionId);
      }

      const response = await api.post('/api/ingest/documents/batch', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getIngestionStatus(taskId = null, userSessionId = null) {
    try {
      const params = new URLSearchParams();
      if (taskId) params.append('task_id', taskId);
      if (userSessionId) params.append('user_session_id', userSessionId);

      const response = await api.get(`/api/ingest/status?${params.toString()}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Query Processing APIs
  async processQuery(query, userContext = null, queryType = null) {
    try {
      const response = await api.post('/api/query/', {
        query,
        user_context: userContext,
        query_type: queryType
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async classifyQuery(query, userContext = null) {
    try {
      const response = await api.post('/api/query/classify', {
        query,
        user_context: userContext
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async generateSQL(query, schemaInfo = null, userContext = null) {
    try {
      const response = await api.post('/api/query/sql', {
        query,
        schema_info: schemaInfo,
        user_context: userContext
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async searchDocuments(query, docType = null, limit = 10, filters = null) {
    try {
      const response = await api.post('/api/query/documents', {
        query,
        doc_type: docType,
        limit,
        filters
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getQueryHistory(limit = 10, offset = 0) {
    try {
      const response = await api.get(`/api/query/history?limit=${limit}&offset=${offset}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getQueryStats() {
    try {
      const response = await api.get('/api/query/stats');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Schema Management APIs
  async getSchema() {
    try {
      const response = await api.get('/api/schema');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async refreshSchema() {
    try {
      const response = await api.post('/api/schema/refresh');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getSchemaVisualization(includeRelationships = true, includeMetadata = true) {
    try {
      const response = await api.post('/api/schema/visualization', {
        include_relationships: includeRelationships,
        include_metadata: includeMetadata
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async exportSchema() {
    try {
      const response = await api.get('/api/schema/export');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async validateSchema() {
    try {
      const response = await api.post('/api/schema/validate');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Document Search APIs
  async searchDocuments(query, docType = null, limit = 10, filters = null) {
    try {
      const response = await api.post('/api/ingest/search', {
        query,
        doc_type: docType,
        limit,
        filters
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getDocumentCollections() {
    try {
      const response = await api.get('/api/ingest/collections');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // System Health APIs
  async getSystemHealth() {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getComprehensiveHealth() {
    try {
      const response = await api.get('/health/comprehensive');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getHealthAlerts() {
    try {
      const response = await api.get('/health/alerts');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getHealthHistory(hours = 24) {
    try {
      const response = await api.get(`/health/history?hours=${hours}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Utility Methods
  handleError(error) {
    console.error('API Service Error:', error);
    
    // Return structured error object
    if (error.type) {
      return error; // Already structured
    }
    
    // Structure unknown error
    return {
      type: 'unknown_error',
      message: error.message || 'An unknown error occurred',
      code: 'UNKNOWN_ERROR',
      originalError: error
    };
  }

  // File Upload Helper
  createFileUploadFormData(files, additionalData = {}) {
    const formData = new FormData();
    
    // Add files
    files.forEach((file, index) => {
      formData.append('files', file);
    });
    
    // Add additional data
    Object.keys(additionalData).forEach(key => {
      if (additionalData[key] !== null && additionalData[key] !== undefined) {
        formData.append(key, additionalData[key]);
      }
    });
    
    return formData;
  }

  // Query Parameter Helper
  buildQueryParams(params) {
    const searchParams = new URLSearchParams();
    
    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined) {
        searchParams.append(key, params[key]);
      }
    });
    
    return searchParams.toString();
  }
}

// Create and export API service instance
const apiService = new ApiService();
export default apiService;

// Export individual methods for convenience
export const {
  getHealth,
  connectDatabase,
  testDatabaseConnection,
  uploadDocuments,
  batchUploadDocuments,
  getIngestionStatus,
  processQuery,
  classifyQuery,
  generateSQL,
  searchDocuments,
  getQueryHistory,
  getQueryStats,
  getSchema,
  refreshSchema,
  getSchemaVisualization,
  exportSchema,
  validateSchema,
  getDocumentCollections,
  getSystemHealth,
  getComprehensiveHealth,
  getHealthAlerts,
  getHealthHistory
} = apiService;
