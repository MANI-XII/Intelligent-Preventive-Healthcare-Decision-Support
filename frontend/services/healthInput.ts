import { predict } from "./api";

export type HealthInput = {
  gender: "Male" | "Female" | "Other";
  age: number;
  bmi: number;
  blood_glucose_level: number;
  hba1c_level: number;
  blood_pressure?: string;
  smoking_history: "never" | "former" | "current";
  hypertension: number;
  heart_disease: number;
  activity_level: "low" | "moderate" | "high";
  sleep_hours: number;
  stress_level: "low" | "moderate" | "high";
  diet_type: "balanced" | "high-carb" | "high-fat" | "low-sugar" | "vegetarian" | "other";
};

export type PredictionResult = {
  overall_risk_score: number;
  overall_risk_level: string;
  health_index: {
    score: number;
    category: string;
    components?: Record<string, number>;
  };
  health_category: string;
  risk_forecast?: Array<{
    months_ahead: number;
    diabetes_risk: number;
    heart_disease_risk: number;
    hypertension_risk: number;
  }>;
  dependency_explanations?: string[];
  grouped_scores?: {
    metabolic: Array<{ id: string; name: string; probability: number; risk_level: string; confidence?: number; status?: string }>;
    cardiovascular: Array<{ id: string; name: string; probability: number; risk_level: string; confidence?: number; status?: string }>;
    other: Array<{ id: string; name: string; probability: number; risk_level: string; confidence?: number; status?: string }>;
  };
  explanations?: {
    shap_chart_base64?: string;
    contributions?: Record<string, number>;
    feature_importance?: Record<string, number>;
  };
  recommendations?: string[];
  anomalies?: { anomaly_detected: boolean; anomalies?: string[] };
  confidence?: { overall: number };
  prediction_id?: number;
  disease_scores?: Record<string, { probability: number; risk_level: string; confidence: number; status?: string }>;
};

export const defaultHealthInput: HealthInput = {
  gender: "Male",
  age: 40,
  bmi: 28,
  blood_glucose_level: 110,
  hba1c_level: 5.8,
  blood_pressure: "",
  smoking_history: "never",
  hypertension: 0,
  heart_disease: 0,
  activity_level: "moderate",
  sleep_hours: 7,
  stress_level: "moderate",
  diet_type: "balanced",
};

function inputStorageKey(userId: string | null) {
  return `userHealthInput-${userId || "anonymous"}`;
}

function predictionStorageKey(userId: string | null) {
  return `latestPrediction-${userId || "anonymous"}`;
}

function parseStoredValue<T>(raw: string | null): T | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function saveInput(userId: string | null, inputData: HealthInput) {
  window.localStorage.setItem(inputStorageKey(userId), JSON.stringify(inputData));
}

export function loadInput(userId: string | null): HealthInput | null {
  return parseStoredValue<HealthInput>(window.localStorage.getItem(inputStorageKey(userId)));
}

export function saveLatestPrediction(userId: string | null, result: PredictionResult) {
  window.localStorage.setItem(predictionStorageKey(userId), JSON.stringify(result));
}

export function loadLatestPrediction(userId: string | null): PredictionResult | null {
  return parseStoredValue<PredictionResult>(window.localStorage.getItem(predictionStorageKey(userId)));
}

export function clearHealthData(userId: string | null) {
  // Keep Prediction and Simulation in sync by clearing the shared source of truth.
  window.localStorage.removeItem(inputStorageKey(userId));
  window.localStorage.removeItem(predictionStorageKey(userId));
}

export async function runPrediction(inputData: HealthInput): Promise<PredictionResult> {
  return (await predict(inputData)) as PredictionResult;
}

export async function runSimulation(modifiedInput: HealthInput): Promise<PredictionResult> {
  // Simulation reuses the same prediction endpoint but never persists until Apply is clicked.
  return runPrediction(modifiedInput);
}
