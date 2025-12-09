import axios from 'axios';

// Create axios instance with FastAPI backend
const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
    headers: {
        'Content-Type': 'application/json',
    }
});

// ==================== Health & Status ====================

/**
 * Check API health status
 */
export const checkHealth = () => api.get('/health');

/**
 * Get validation statistics
 */
export const getStats = () => api.get('/stats');

// ==================== Single Provider Validation ====================

/**
 * Validate a single provider
 * @param {Object} providerData - Provider information
 */
export const validateProvider = (providerData) =>
    api.post('/validate', providerData);

/**
 * Validate multiple providers in batch
 * @param {Object} batchRequest - Batch validation request
 */
export const validateBatch = (batchRequest) =>
    api.post('/validate/batch', batchRequest);

/**
 * Get batch validation status
 * @param {string} batchId - Batch job ID
 */
export const getBatchStatus = (batchId) =>
    api.get(`/batch/${batchId}`);

// ==================== File Upload ====================

/**
 * Upload provider list file (PDF or Excel)
 * @param {File} file - File to upload
 */
export const uploadFile = (file) => {
    const formData = new FormData();
    formData.append('file', file);

    return api.post('/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        }
    });
};

/**
 * Validate all providers from uploaded file
 * @param {string} fileId - File ID from upload
 * @param {string} priority - Job priority (normal, high, low)
 */
export const validateUploadedFile = (fileId, priority = 'normal') =>
    api.post(`/upload/${fileId}/validate`, null, {
        params: { priority }
    });

// ==================== Provider Details ====================

/**
 * Get validation result for a specific provider
 * @param {string} providerId - Provider ID
 */
export const getProviderResult = (providerId) =>
    api.get(`/validate/${providerId}`);

/**
 * Get all providers from a batch
 * @param {string} batchId - Batch ID
 */
export const getBatchProviders = (batchId) =>
    api.get(`/batch/${batchId}`);

// ==================== Webhook Support ====================

/**
 * Test webhook connectivity
 * @param {string} webhookUrl - Webhook URL to test
 */
export const testWebhook = (webhookUrl) =>
    api.post('/webhook/test', null, {
        params: { webhook_url: webhookUrl }
    });

// ==================== Error Handler ====================

// Add response interceptor for error handling
api.interceptors.response.use(
    response => response,
    error => {
        if (error.response) {
            // Server responded with error status
            console.error('API Error:', error.response.status, error.response.data);
        } else if (error.request) {
            // Request made but no response
            console.error('No response from API:', error.request);
        } else {
            // Something else happened
            console.error('Error:', error.message);
        }
        return Promise.reject(error);
    }
);

export default api;

