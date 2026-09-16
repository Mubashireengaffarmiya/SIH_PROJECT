import axios from 'axios';
import type {
  AnalysisResponse,
  DashboardStats,
  InspectionDetail,
  InspectionSummary,
} from '../types';

const apiBaseUrl = import.meta.env.VITE_API_URL ?? '';

// When using Vite proxy, /api routes go to localhost:8000 automatically
const api = axios.create({
  baseURL: apiBaseUrl,
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
// Authentication
// ---------------------------------------------------------------------------
export const login = async (username: string, password: string) => {
  const formData = new URLSearchParams({ username, password });
  const res = await api.post<{
    access_token: string;
    token_type: string;
    role: string;
    username: string;
  }>('/api/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return res.data;
};

// ---------------------------------------------------------------------------
// Analysis
// ---------------------------------------------------------------------------
export const analyzeImage = async (
  file: File,
  context: { origin: string; package_type: string; sales_channel: string },
): Promise<AnalysisResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('origin', context.origin);
  formData.append('package_type', context.package_type);
  formData.append('sales_channel', context.sales_channel);
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

// ---------------------------------------------------------------------------
// Review workflow
// ---------------------------------------------------------------------------
export const getReviewQueue = async (): Promise<InspectionSummary[]> => {
  const res = await api.get<InspectionSummary[]>('/api/reviewer/queue');
  return res.data;
};

export const reviewInspection = async (inspectionId: string, action: string, comment = '') => {
  const res = await api.post<{ status: string; message: string }>(
    `/api/reviewer/inspections/${inspectionId}/review`,
    { action, comment }
  );
  return res.data;
};

// ---------------------------------------------------------------------------
// Administration
// ---------------------------------------------------------------------------
export interface AdminUser {
  id: number;
  username: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface AuditLog {
  id: number;
  username: string;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  detail: string | null;
  timestamp: string;
}

export const listAdminUsers = async (): Promise<AdminUser[]> => {
  const res = await api.get<AdminUser[]>('/api/admin/users');
  return res.data;
};

export const listAuditLogs = async (): Promise<AuditLog[]> => {
  const res = await api.get<AuditLog[]>('/api/admin/audit_logs');
  return res.data;
};
