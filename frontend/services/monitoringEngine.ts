import { loadLatestPrediction } from "./healthInput";

export type AlertLevel = "NORMAL" | "WARNING" | "HIGH_RISK" | "CRITICAL";
export type TrendDirection = "increasing" | "decreasing" | "stable";

export type VitalsRecord = {
  timestamp: string;
  heart_rate_bpm: number;
  systolic_bp: number;
  diastolic_bp: number;
  oxygen_level: number;
  body_temperature_c: number;
  risk_percentage: number;
  source: "manual" | "simulated";
};

export type TrendSummary = {
  heart_rate_bpm: TrendDirection;
  blood_pressure: TrendDirection;
  oxygen_level: TrendDirection;
  body_temperature_c: TrendDirection;
  risk_percentage: TrendDirection;
};

export type MonitoringAlert = {
  id: string;
  level: AlertLevel;
  condition_key: string;
  message: string;
  vitals: VitalsRecord;
  recommendation: string[];
  trend_summary: TrendSummary;
  related_goal: string | null;
  timestamp: string;
};

const MAX_HISTORY = 24;
const HISTORY_KEY_PREFIX = "monitoringVitalsHistory";
const ALERT_KEY_PREFIX = "monitoringAlertHistory";
const BASELINE_KEY_PREFIX = "monitoringManualBaseline";

function historyKey(userId: string | null) {
  return `${HISTORY_KEY_PREFIX}-${userId || "anonymous"}`;
}

function alertKey(userId: string | null) {
  return `${ALERT_KEY_PREFIX}-${userId || "anonymous"}`;
}

function baselineKey(userId: string | null) {
  return `${BASELINE_KEY_PREFIX}-${userId || "anonymous"}`;
}

function parseStoredValue<T>(raw: string | null): T | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function round1(value: number) {
  return Math.round(value * 10) / 10;
}

function randomOffset(span: number) {
  return (Math.random() - 0.5) * span;
}

export function loadVitalsHistory(userId: string | null) {
  return parseStoredValue<VitalsRecord[]>(window.localStorage.getItem(historyKey(userId))) || [];
}

export function saveVitalsHistory(userId: string | null, history: VitalsRecord[]) {
  window.localStorage.setItem(historyKey(userId), JSON.stringify(history.slice(-MAX_HISTORY)));
}

export function loadAlertHistory(userId: string | null) {
  return parseStoredValue<MonitoringAlert[]>(window.localStorage.getItem(alertKey(userId))) || [];
}

export function saveAlertHistory(userId: string | null, history: MonitoringAlert[]) {
  window.localStorage.setItem(alertKey(userId), JSON.stringify(history.slice(-MAX_HISTORY)));
}

export function saveManualBaseline(userId: string | null, vitals: Partial<VitalsRecord>) {
  window.localStorage.setItem(baselineKey(userId), JSON.stringify(vitals));
}

export function loadManualBaseline(userId: string | null) {
  return parseStoredValue<Partial<VitalsRecord>>(window.localStorage.getItem(baselineKey(userId))) || null;
}

function compareDirection(current: number, previous: number, epsilon: number) {
  if (current > previous + epsilon) return "increasing";
  if (current < previous - epsilon) return "decreasing";
  return "stable";
}

export function detectTrend(history: VitalsRecord[]): TrendSummary {
  if (!history.length) {
    return {
      heart_rate_bpm: "stable",
      blood_pressure: "stable",
      oxygen_level: "stable",
      body_temperature_c: "stable",
      risk_percentage: "stable",
    };
  }
  const current = history[history.length - 1];
  const previous = history[Math.max(0, history.length - 2)] || current;
  return {
    heart_rate_bpm: compareDirection(current.heart_rate_bpm, previous.heart_rate_bpm, 2),
    blood_pressure: compareDirection(current.systolic_bp, previous.systolic_bp, 2),
    oxygen_level: compareDirection(current.oxygen_level, previous.oxygen_level, 1),
    body_temperature_c: compareDirection(current.body_temperature_c, previous.body_temperature_c, 0.2),
    risk_percentage: compareDirection(current.risk_percentage, previous.risk_percentage, 3),
  };
}

function createRecommendation(level: AlertLevel, vitals: VitalsRecord) {
  const recommendations = new Set<string>();
  if (level === "WARNING") {
    recommendations.add("Take rest and monitor your symptoms closely.");
  }
  if (level === "HIGH_RISK" || level === "CRITICAL") {
    recommendations.add("Consult doctor.");
  }
  if (vitals.oxygen_level < 94) {
    recommendations.add("Check oxygen levels again in a few minutes.");
  }
  if (vitals.heart_rate_bpm > 100) {
    recommendations.add("Sit down, hydrate, and avoid exertion.");
  }
  if (vitals.body_temperature_c > 38) {
    recommendations.add("Take rest and monitor your temperature.");
  }
  if (level === "CRITICAL") {
    recommendations.add("Seek urgent medical support if symptoms persist.");
  }
  return Array.from(recommendations).slice(0, 3);
}

export function generateAlert(
  level: AlertLevel,
  message: string,
  vitals: VitalsRecord,
  trendSummary: TrendSummary,
  conditionKey: string,
  relatedGoal: string | null
): MonitoringAlert {
  return {
    id: `${conditionKey}-${vitals.timestamp}`,
    level,
    condition_key: conditionKey,
    message,
    vitals,
    recommendation: createRecommendation(level, vitals),
    trend_summary: trendSummary,
    related_goal: relatedGoal,
    timestamp: vitals.timestamp,
  };
}

function alertSeverity(level: AlertLevel) {
  if (level === "CRITICAL") return 4;
  if (level === "HIGH_RISK") return 3;
  if (level === "WARNING") return 2;
  return 1;
}

export function preventDuplicateAlert(lastAlert: MonitoringAlert | null, nextAlert: MonitoringAlert) {
  if (!lastAlert) return true;
  if (lastAlert.condition_key !== nextAlert.condition_key) return true;
  if (lastAlert.level !== nextAlert.level) return true;
  const worsened =
    nextAlert.vitals.heart_rate_bpm > lastAlert.vitals.heart_rate_bpm + 5 ||
    nextAlert.vitals.oxygen_level < lastAlert.vitals.oxygen_level - 1 ||
    nextAlert.vitals.body_temperature_c > lastAlert.vitals.body_temperature_c + 0.3 ||
    alertSeverity(nextAlert.level) > alertSeverity(lastAlert.level);
  return worsened;
}

function simulateVitals(
  previous: VitalsRecord | null,
  riskPercentage: number,
  baseline: Partial<VitalsRecord> | null
): VitalsRecord {
  const baseHeartRate = baseline?.heart_rate_bpm ?? previous?.heart_rate_bpm ?? 76;
  const baseSystolic = baseline?.systolic_bp ?? previous?.systolic_bp ?? 122;
  const baseDiastolic = baseline?.diastolic_bp ?? previous?.diastolic_bp ?? 80;
  const baseOxygen = baseline?.oxygen_level ?? previous?.oxygen_level ?? 97;
  const baseTemp = baseline?.body_temperature_c ?? previous?.body_temperature_c ?? 36.8;
  const riskDrift = riskPercentage >= 80 ? 1.8 : riskPercentage >= 60 ? 1.0 : 0.4;

  return {
    timestamp: new Date().toISOString(),
    heart_rate_bpm: Math.round(clamp(baseHeartRate + randomOffset(8) + riskDrift, 58, 132)),
    systolic_bp: Math.round(clamp(baseSystolic + randomOffset(10) + riskDrift * 2, 100, 170)),
    diastolic_bp: Math.round(clamp(baseDiastolic + randomOffset(6) + riskDrift, 60, 110)),
    oxygen_level: round1(clamp(baseOxygen + randomOffset(2) - riskDrift * 0.3, 87, 100)),
    body_temperature_c: round1(clamp(baseTemp + randomOffset(0.6) + riskDrift * 0.05, 35.8, 39.5)),
    risk_percentage: round1(riskPercentage),
    source: baseline ? "manual" : "simulated",
  };
}

export function evaluateAlert(vitals: VitalsRecord, riskPercentage: number, history: VitalsRecord[]) {
  const trendSummary = detectTrend(history);
  const issues: string[] = [];
  let level: AlertLevel = "NORMAL";
  let conditionKey = "normal";

  if (vitals.heart_rate_bpm > 120) {
    level = "HIGH_RISK";
    conditionKey = "heart-rate-high-risk";
    issues.push("Heart rate is very high");
  } else if (vitals.heart_rate_bpm > 100) {
    level = "WARNING";
    conditionKey = "heart-rate-warning";
    issues.push("Heart rate is slightly elevated");
  }

  if (vitals.oxygen_level < 90) {
    level = "CRITICAL";
    conditionKey = "oxygen-critical";
    issues.push("Oxygen level is critically low");
  } else if (vitals.oxygen_level < 94 && alertSeverity(level) < alertSeverity("HIGH_RISK")) {
    level = "HIGH_RISK";
    conditionKey = "oxygen-high-risk";
    issues.push("Oxygen level is low");
  }

  if (vitals.body_temperature_c > 38 && alertSeverity(level) < alertSeverity("WARNING")) {
    level = "WARNING";
    conditionKey = "temperature-warning";
    issues.push("Temperature is above the normal range");
  }

  if (riskPercentage > 80 && alertSeverity(level) < alertSeverity("HIGH_RISK")) {
    level = "HIGH_RISK";
    conditionKey = "prediction-high-risk";
    issues.push("Prediction risk is very high");
  }

  if (riskPercentage > 80 && vitals.oxygen_level < 94) {
    level = "CRITICAL";
    conditionKey = "risk-oxygen-critical";
    issues.push("High prediction risk and low oxygen detected together");
  }

  const abnormalVitals = [
    vitals.heart_rate_bpm > 100,
    vitals.oxygen_level < 94,
    vitals.body_temperature_c > 38,
    vitals.systolic_bp > 140,
  ].filter(Boolean).length;

  if (abnormalVitals >= 2 && alertSeverity(level) < alertSeverity("HIGH_RISK")) {
    level = "HIGH_RISK";
    conditionKey = "multiple-abnormal-vitals";
    issues.push("Multiple vitals are outside the safe range");
  }

  if (trendSummary.risk_percentage === "increasing" && alertSeverity(level) < alertSeverity("WARNING")) {
    level = "WARNING";
    conditionKey = "risk-trend-warning";
    issues.push("Prediction risk is trending upward");
  }

  if (trendSummary.oxygen_level === "decreasing" && vitals.oxygen_level < 95 && alertSeverity(level) < alertSeverity("HIGH_RISK")) {
    level = "HIGH_RISK";
    conditionKey = "oxygen-dropping";
    issues.push("Oxygen is dropping over time");
  }

  if (trendSummary.heart_rate_bpm === "increasing" && vitals.heart_rate_bpm > 95 && alertSeverity(level) < alertSeverity("WARNING")) {
    level = "WARNING";
    conditionKey = "heart-rate-rising";
    issues.push("Heart rate is rising");
  }

  const message =
    issues.length > 0
      ? issues[0] + (issues.length > 1 ? `, plus ${issues.length - 1} more signal${issues.length > 2 ? "s" : ""}.` : ".")
      : "All monitored vitals are within the safe range.";

  return { level, message, trendSummary, conditionKey };
}

export function monitorPatient(args: {
  userId: string | null;
  previousHistory: VitalsRecord[];
  previousAlerts: MonitoringAlert[];
  riskPercentage: number;
  relatedGoal: string | null;
}) {
  const baseline = loadManualBaseline(args.userId);
  const previous = args.previousHistory[args.previousHistory.length - 1] || null;
  const vitals = simulateVitals(previous, args.riskPercentage, baseline);
  const nextHistory = [...args.previousHistory, vitals].slice(-MAX_HISTORY);
  const evaluation = evaluateAlert(vitals, args.riskPercentage, nextHistory);
  const nextAlert = generateAlert(
    evaluation.level,
    evaluation.message,
    vitals,
    evaluation.trendSummary,
    evaluation.conditionKey,
    args.relatedGoal
  );
  const lastAlert = args.previousAlerts[args.previousAlerts.length - 1] || null;
  const shouldAppendAlert = preventDuplicateAlert(lastAlert, nextAlert);
  const nextAlerts = shouldAppendAlert ? [...args.previousAlerts, nextAlert].slice(-MAX_HISTORY) : args.previousAlerts;

  saveVitalsHistory(args.userId, nextHistory);
  saveAlertHistory(args.userId, nextAlerts);

  return {
    vitals,
    vitalsHistory: nextHistory,
    alertHistory: nextAlerts,
    latestAlert: nextAlerts[nextAlerts.length - 1] || nextAlert,
    trends: evaluation.trendSummary,
  };
}

export function getCurrentRisk(userId: string | null) {
  const prediction = loadLatestPrediction(userId);
  return prediction ? Math.round(prediction.overall_risk_score) : 0;
}
