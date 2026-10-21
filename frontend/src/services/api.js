import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

export const apiService = {
  // System Health & Model Status
  getHealth: async () => {
    const response = await apiClient.get('/api/health');
    return response.data;
  },

  getModelStatus: async () => {
    const response = await apiClient.get('/api/model-status');
    return response.data;
  },

  // Students
  getStudents: async () => {
    const response = await apiClient.get('/api/students');
    return response.data;
  },

  getStudentById: async (studentId) => {
    const response = await apiClient.get(`/api/students/${studentId}`);
    return response.data;
  },

  // Questions
  getQuestions: async () => {
    const response = await apiClient.get('/api/questions');
    return response.data;
  },

  // Answers
  getStudentAnswers: async (studentId) => {
    const response = await apiClient.get(`/api/students/${studentId}/answers`);
    return response.data;
  },

  // AI & Feedback Analysis
  analyzeAnswer: async (payload) => {
    const response = await apiClient.post('/api/analyze-answer', payload);
    return response.data;
  },

  // Feedback & Recommendations
  getStudentFeedback: async (studentId) => {
    const response = await apiClient.get(`/api/students/${studentId}/feedback`);
    return response.data;
  },

  getStudentRecommendations: async (studentId) => {
    const response = await apiClient.get(`/api/students/${studentId}/recommendations`);
    return response.data;
  },

  // Dataset Operations
  uploadDataset: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/api/import-dataset', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  seedDemoData: async () => {
    const response = await apiClient.post('/api/seed-demo-data');
    return response.data;
  },

  // Research Component: Concept Dependency Analysis
  getCurriculumDependencies: async () => {
    const response = await apiClient.get('/api/concept-dependencies');
    return response.data;
  },

  getStudentDependencies: async (studentId) => {
    const response = await apiClient.get(`/api/students/${studentId}/concept-dependencies`);
    return response.data;
  },

  predictMissingConcepts: async (payload) => {
    const response = await apiClient.post('/api/predict-missing-concepts', payload);
    return response.data;
  },

  // Dynamic Dashboard statistics (real per-student data)
  getDashboardStats: async (studentId) => {
    const response = await apiClient.get(`/api/students/${studentId}/dashboard`);
    return response.data;
  },

  getStudentDashboard: async (studentId) => {
    const response = await apiClient.get(`/api/students/${studentId}/dashboard`);
    return response.data;
  },

  // Lectures
  getLectures: async () => {
    const response = await apiClient.get('/api/lectures');
    return response.data;
  },
};

export default apiClient;
