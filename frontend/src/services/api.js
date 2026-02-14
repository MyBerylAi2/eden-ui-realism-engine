/**
 * EDEN UI REALISM ENGINE - API Service
 * =====================================
 * Axios-based API client for the backend.
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Model Management
export const searchModels = (query = '', modelType = 'text-to-image', limit = 50) =>
  api.get('/api/models/search', { params: { query, model_type: modelType, limit } });

export const getModelInfo = (modelId) =>
  api.get(`/api/models/info/${modelId}`);

export const downloadModel = (modelId) =>
  api.post('/api/models/download', { model_id: modelId });

export const listDownloadedModels = () =>
  api.get('/api/models/downloaded');

export const getRecommendedModels = () =>
  api.get('/api/models/recommended');

// Generation
export const generateImage = (params) =>
  api.post('/api/generate/image', params);

export const generateVideo = (params) =>
  api.post('/api/generate/video', params);

export const imageToVideo = (params) =>
  api.post('/api/generate/image-to-video', params);

// File Upload
export const uploadFile = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

// Chat
export const sendChatMessage = (message, sessionId = null, attachments = null) =>
  api.post('/api/chat', { message, session_id: sessionId, attachments });

// EDEN Configuration
export const getNegativeKeywords = (category = 'all') =>
  api.get('/api/eden/negative-keywords', { params: { category } });

export const getNegativeCategories = () =>
  api.get('/api/eden/negative-categories');

export const getPresets = () =>
  api.get('/api/eden/presets');

export const getPreset = (presetName) =>
  api.get(`/api/eden/presets/${presetName}`);

export const getEnhancements = () =>
  api.get('/api/eden/enhancements');

// System
export const getSystemStatus = () =>
  api.get('/api/system/status');

export const unloadModel = (modelId = null) =>
  api.post('/api/system/unload-model', { model_id: modelId });

// ComfyUI
export const getComfyUIStatus = () =>
  api.get('/api/comfyui/status');

export const executeComfyUIWorkflow = (workflow) =>
  api.post('/api/comfyui/execute', workflow);

export default api;
