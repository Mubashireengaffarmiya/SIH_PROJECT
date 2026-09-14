import axios from 'axios';
import type {
  AnalysisResponse,
  DashboardStats,
  InspectionDetail,
  InspectionSummary,
} from '../types';

// When using Vite proxy, /api routes go to localhost:8000 automatically
const api = axios.create({
  baseURL: '',
  timeout: 120000, // 2 min — OCR can be slow on first load
  headers: {
    Accept: 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------
export const checkHealth = () => api.get<{ status: string }>('/api/health');

// ---------------------------------------------------------------------------
// Analysis
// ---------------------------------------------------------------------------
export const analyzeImage = async (file: File): Promise<AnalysisResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post<AnalysisResponse>('/api/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

// ---------------------------------------------------------------------------
// Inspections
// ---------------------------------------------------------------------------
export const listInspections = async (): Promise<InspectionSummary[]> => {
  const res = await api.get<InspectionSummary[]>('/api/inspections');
  return res.data;
};

export const getInspection = async (id: string): Promise<InspectionDetail> => {
  const res = await api.get<InspectionDetail>(`/api/inspections/${id}`);
  return res.data;
};

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------
export const getDashboard = async (): Promise<DashboardStats> => {
  const res = await api.get<DashboardStats>('/api/dashboard');
  return res.data;
};

// ---------------------------------------------------------------------------
// Reports
// ---------------------------------------------------------------------------
export const downloadPdfReport = async (inspectionId: string): Promise<void> => {
  const res = await api.post(`/api/reports/${inspectionId}/pdf`, null, {
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `SMART-LM-Report-${inspectionId}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const downloadDocxReport = async (inspectionId: string): Promise<void> => {
  const res = await api.post(`/api/reports/${inspectionId}/docx`, null, {
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(
    new Blob([res.data], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })
  );
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `SMART-LM-Report-${inspectionId}.docx`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};
