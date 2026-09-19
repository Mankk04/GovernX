import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("governx_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface MaturityScore {
  function_id: string;
  function_name: string;
  tier_level: number;
  calculated_at: string;
}

export interface RiskSummary {
  org_id: string;
  total_value_at_risk: number;
  total_annualized_loss_expectancy: number;
  top_findings: {
    finding_id: string;
    resource: string;
    subcategory: string;
    value_at_risk: number;
    severity: string | null;
  }[];
  generated_at: string;
}

export interface Finding {
  finding_id: string;
  account_id: string;
  resource_type: string | null;
  resource_identifier: string | null;
  subcategory_id: string | null;
  finding_status: string;
  severity: string | null;
  scanned_at: string;
}

export interface CloudAccount {
  account_id: string;
  provider: string;
  account_identifier: string;
  created_at: string;
}

export async function login(email: string, password: string) {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  const res = await apiClient.post("/api/v1/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return res.data as { access_token: string; role: string; org_id: string };
}

export const getScores = () => apiClient.get<MaturityScore[]>("/api/v1/scores").then((r) => r.data);
export const getRiskSummary = () => apiClient.get<RiskSummary>("/api/v1/risk/summary").then((r) => r.data);
export const getFindings = (params?: Record<string, string>) =>
  apiClient.get<Finding[]>("/api/v1/findings", { params }).then((r) => r.data);
export const getAccounts = () => apiClient.get<CloudAccount[]>("/api/v1/accounts").then((r) => r.data);
export const registerAccount = (provider: string, account_identifier: string) =>
  apiClient.post<CloudAccount>("/api/v1/accounts", { provider, account_identifier }).then((r) => r.data);
export const triggerScan = (accountId: string) =>
  apiClient.post(`/api/v1/findings/scan/${accountId}`).then((r) => r.data);
export const acknowledgeFinding = (findingId: string, justification: string) =>
  apiClient.patch(`/api/v1/findings/${findingId}/acknowledge`, { justification }).then((r) => r.data);
export const generateReport = () =>
  apiClient.post("/api/v1/reports/generate").then((r) => r.data);
