import axios from "axios";
import { getStoredToken } from "./auth";

const baseURL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://preventive-health-api.onrender.com";

export const api = axios.create({
  baseURL,
  timeout: 120000,
});

export const APP_DATA_CHANGED_EVENT = "app-data-changed";

function emitAppDataChanged(scope: string) {
  if (typeof window === "undefined") return;

  window.dispatchEvent(
    new CustomEvent(APP_DATA_CHANGED_EVENT, {
      detail: { scope, at: Date.now() },
    })
  );
}

const abortControllers = new Map<string, AbortController>();

api.interceptors.request.use((config) => {
  const token = getStoredToken();

  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

function createRequestKey(method: string, url: string): string {
  return `${method}:${url}`;
}

export function cancelAllRequests() {
  abortControllers.forEach((controller) => {
    controller.abort();
  });

  abortControllers.clear();
}

export function cancelRequest(key: string) {
  const controller = abortControllers.get(key);

  if (controller) {
    controller.abort();
    abortControllers.delete(key);
  }
}

export async function predict(payload: any) {
  const res = await api.post("/predict", payload);
  return res.data;
}

export async function predictMulti(payload: any) {
  const res = await api.post("/predict/multi", payload);
  return res.data;
}

export async function getHealthScore() {
  const res = await api.get("/health-score");
  return res.data;
}

export async function getAlerts() {
  const res = await api.get("/alerts");
  return res.data;
}

export async function ackAlert(payload: any) {
  const res = await api.post("/alerts/ack", payload);
  return res.data;
}

export async function getProfile() {
  const res = await api.get("/profile");
  return res.data;
}

export async function updateProfile(payload: any) {
  const res = await api.put("/profile", payload);
  emitAppDataChanged("profile");
  return res.data;
}

export async function addDeviceReading(payload: any) {
  const res = await api.post("/devices/data", payload);
  return res.data;
}

export async function getLatestDeviceReading() {
  const res = await api.get("/devices/latest");
  return res.data;
}

export async function listGoals() {
  const res = await api.get("/goals");
  return res.data;
}

export async function createGoal(payload: any) {
  const res = await api.post("/goals", payload);
  emitAppDataChanged("goals");
  return res.data;
}

export async function updateGoal(payload: any) {
  const res = await api.patch("/goals", payload);
  emitAppDataChanged("goals");
  return res.data;
}

export async function deleteGoal(goalId: number) {
  const res = await api.delete(`/goals/${goalId}`);
  emitAppDataChanged("goals");
  return res.data;
}

export async function getGamification() {
  const res = await api.get("/gamification");
  return res.data;
}

export async function addBehavior(payload: any) {
  const res = await api.post("/behavior", payload);
  return res.data;
}

export async function listBehavior() {
  const res = await api.get("/behavior");
  return res.data;
}

export async function chat(payload: any) {
  const res = await api.post("/chat", payload);
  return res.data;
}

export async function simulate(payload: any) {
  const res = await api.post("/simulate", payload);
  return res.data;
}

export async function addTask(payload: any) {
  const res = await api.post("/tasks", payload);
  emitAppDataChanged("tasks");
  return res.data;
}

export async function updateTask(payload: any) {
  const res = await api.post("/tasks/update", payload);
  emitAppDataChanged("tasks");
  return res.data;
}

export async function deleteTask(taskId: number) {
  const res = await api.delete(`/tasks/${taskId}`);
  emitAppDataChanged("tasks");
  return res.data;
}

export async function deleteAllTasks() {
  const res = await api.delete("/tasks");
  emitAppDataChanged("tasks");
  return res.data;
}

export async function rescheduleTask(taskId: number) {
  const res = await api.post(`/tasks/${taskId}/reschedule`);
  emitAppDataChanged("tasks");
  return res.data;
}

export async function getTaskRescheduleOptions(taskId: number) {
  const res = await api.get(`/tasks/${taskId}/reschedule-options`);
  return res.data;
}

export async function rescheduleTaskToDate(taskId: number, targetDate: string) {
  const res = await api.post(`/tasks/${taskId}/reschedule`, {
    target_date: targetDate,
  });

  emitAppDataChanged("tasks");

  return res.data;
}

export async function getProgress() {
  const res = await api.get("/progress");
  return res.data;
}

export async function createHealthRecord(payload: any) {
  const res = await api.post("/health-data", payload);
  emitAppDataChanged("health-record");
  return res.data;
}

export async function getLatestHealthRecord() {
  const res = await api.get("/health-data/latest");
  return res.data;
}

export async function getPredictionHistory() {
  const res = await api.get("/health-data/history");
  return res.data;
}

export async function getPredictionTrend() {
  const res = await api.get("/health-data/trend");
  return res.data;
}

export async function downloadReport(predictionId?: number) {
  const token = getStoredToken();

  const url = predictionId
    ? `${baseURL}/report?prediction_id=${predictionId}`
    : `${baseURL}/report`;

  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to download report");
  }

  return res.blob();
}

export async function generateExplanation(healthData: any) {
  const res = await api.post("/ai/explain", healthData);
  return res.data;
}

export async function generateRecommendations(healthData: any) {
  const res = await api.post("/ai/recommend", healthData);
  return res.data;
}

export async function chatWithAI(message: string) {
  const res = await api.post("/ai/chat", { message });
  return res.data;
}

export async function getHealthInsight() {
  const res = await api.post("/ai/insight");
  return res.data;
}

export async function generateMonitoringReport(
  currentRecord: any,
  daysBack: number = 30
) {
  const res = await api.post("/monitor/report", currentRecord, {
    params: { days_back: daysBack },
  });

  return res.data;
}

export async function getHealthTrends(daysBack: number = 30) {
  const res = await api.get("/monitor/trends", {
    params: { days_back: daysBack },
  });

  return res.data;
}

export async function getMonitoringAlerts() {
  const res = await api.get("/monitor/alerts");
  return res.data;
}