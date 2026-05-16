import { useEffect, useMemo, useRef, useState } from "react";
import DashboardLayout from "../../components/DashboardLayout";
import RequireAuth from "../../components/RequireAuth";
import { useAuth } from "../../context/AuthContext";
import { getGoalDisplayTitle, getGoalMeta } from "../../services/goalAutomation";
import {
  addDeviceReading,
  cancelAllRequests,
  generateMonitoringReport as generateMonitoringReportApi,
  getHealthInsight,
  getHealthScore,
  getLatestHealthRecord,
  getMonitoringAlerts,
  getPredictionHistory,
  getPredictionTrend,
  listGoals,
} from "../../services/api";
import {
  AlertLevel,
  detectTrend,
  getCurrentRisk,
  loadAlertHistory,
  loadVitalsHistory,
  monitorPatient,
  saveManualBaseline,
  type MonitoringAlert,
  type TrendDirection,
  type VitalsRecord,
} from "../../services/monitoringEngine";

type GoalItem = {
  id: number;
  created_at: string;
  goal_type: string;
  target_value: number;
  deadline?: string | null;
  status: string;
  progress_value: number;
  notes?: string | null;
};

function levelClasses(level: AlertLevel) {
  if (level === "CRITICAL") return "border-red-950 bg-red-950 text-red-100";
  if (level === "HIGH_RISK") return "border-red-700 bg-red-950/40 text-red-100";
  if (level === "WARNING") return "border-yellow-700 bg-yellow-950/30 text-yellow-100";
  return "border-emerald-700 bg-emerald-950/20 text-emerald-100";
}

function trendArrow(trend: TrendDirection) {
  if (trend === "increasing") return "↑";
  if (trend === "decreasing") return "↓";
  return "→";
}

function trendTone(trend: TrendDirection, kind: "goodWhenUp" | "goodWhenDown" | "neutral") {
  if (trend === "stable") return "text-slate-400";
  if (kind === "neutral") return trend === "increasing" ? "text-amber-300" : "text-sky-300";
  if (kind === "goodWhenUp") return trend === "increasing" ? "text-emerald-300" : "text-red-300";
  return trend === "decreasing" ? "text-emerald-300" : "text-red-300";
}

function formatBloodPressure(vitals: VitalsRecord | null) {
  if (!vitals) return "—";
  return `${vitals.systolic_bp}/${vitals.diastolic_bp}`;
}

function toRiskPercent(value: number) {
  return `${Math.round(value)}%`;
}

function loadSavedNumber(key: string, fallback: number) {
  if (typeof window === "undefined") return fallback;
  const raw = window.localStorage.getItem(key);
  if (!raw) return fallback;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export default function MonitorPage() {
  const { userId } = useAuth();
  const isMountedRef = useRef(true);
  const monitorIntervalRef = useRef<number | null>(null);

  const [score, setScore] = useState<number | null>(null);
  const [predictionHistory, setPredictionHistory] = useState<any[]>([]);
  const [predictionTrend, setPredictionTrend] = useState<any[]>([]);
  const [backendAlerts, setBackendAlerts] = useState<any[]>([]);
  const [goals, setGoals] = useState<GoalItem[]>([]);

  const [vitalsHistory, setVitalsHistory] = useState<VitalsRecord[]>([]);
  const [alertHistory, setAlertHistory] = useState<MonitoringAlert[]>([]);
  const [liveRisk, setLiveRisk] = useState(0);
  const [latestAlert, setLatestAlert] = useState<MonitoringAlert | null>(null);
  const [liveVitals, setLiveVitals] = useState<VitalsRecord | null>(null);
  const [monitoringActive, setMonitoringActive] = useState(true);

  const [heartRate, setHeartRate] = useState<number>(72);
  const [systolicBP, setSystolicBP] = useState<number>(122);
  const [diastolicBP, setDiastolicBP] = useState<number>(80);
  const [oxygenLevel, setOxygenLevel] = useState<number>(97);
  const [bodyTemperature, setBodyTemperature] = useState<number>(36.8);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  const [aiInsight, setAiInsight] = useState<string | null>(null);
  const [aiInsightBusy, setAiInsightBusy] = useState(false);
  const [monitoringReport, setMonitoringReport] = useState<any>(null);
  const [monitoringBusy, setMonitoringBusy] = useState(false);

  const activeGoalTitle = useMemo(() => {
    const activeGoal = goals.find((goal) => {
      const meta = getGoalMeta(goal);
      return meta && goal.status !== "cancelled";
    });
    return activeGoal ? getGoalDisplayTitle(activeGoal) : null;
  }, [goals]);

  const liveTrends = useMemo(() => detectTrend(vitalsHistory), [vitalsHistory]);

  async function refresh() {
    if (!isMountedRef.current || !userId) return;
    try {
      const [scoreRes, historyRes, trendRes, alertsRes, goalsRes] = await Promise.allSettled([
        getHealthScore(),
        getPredictionHistory(),
        getPredictionTrend(),
        getMonitoringAlerts(),
        listGoals(),
      ]);

      if (!isMountedRef.current) return;

      if (scoreRes.status === "fulfilled") setScore(scoreRes.value?.data?.score ?? null);
      if (historyRes.status === "fulfilled") setPredictionHistory(historyRes.value?.history || []);
      if (trendRes.status === "fulfilled") setPredictionTrend(trendRes.value?.trend || []);
      if (alertsRes.status === "fulfilled") setBackendAlerts(alertsRes.value?.alerts || []);
      if (goalsRes.status === "fulfilled") {
        setGoals((goalsRes.value?.data || []).filter((goal: GoalItem) => goal.status !== "cancelled"));
      }
    } catch (e) {
      console.error("Failed to refresh monitoring dashboard:", e);
    }
  }

  useEffect(() => {
    if (!userId) return;
    isMountedRef.current = true;

    setHeartRate(loadSavedNumber(`monitor-heart-rate-${userId}`, 72));
    setSystolicBP(loadSavedNumber(`monitor-systolic-${userId}`, 122));
    setDiastolicBP(loadSavedNumber(`monitor-diastolic-${userId}`, 80));
    setOxygenLevel(loadSavedNumber(`monitor-oxygen-${userId}`, 97));
    setBodyTemperature(loadSavedNumber(`monitor-temperature-${userId}`, 36.8));

    const storedVitals = loadVitalsHistory(userId);
    const storedAlerts = loadAlertHistory(userId);
    setVitalsHistory(storedVitals);
    setAlertHistory(storedAlerts);
    setLiveVitals(storedVitals[storedVitals.length - 1] || null);
    setLatestAlert(storedAlerts[storedAlerts.length - 1] || null);
    setLiveRisk(getCurrentRisk(userId));
    refresh();

    return () => {
      isMountedRef.current = false;
      if (monitorIntervalRef.current) {
        window.clearInterval(monitorIntervalRef.current);
      }
      cancelAllRequests();
    };
  }, [userId]);

  useEffect(() => {
    if (!userId) return;
    window.localStorage.setItem(`monitor-heart-rate-${userId}`, String(heartRate));
    window.localStorage.setItem(`monitor-systolic-${userId}`, String(systolicBP));
    window.localStorage.setItem(`monitor-diastolic-${userId}`, String(diastolicBP));
    window.localStorage.setItem(`monitor-oxygen-${userId}`, String(oxygenLevel));
    window.localStorage.setItem(`monitor-temperature-${userId}`, String(bodyTemperature));
  }, [userId, heartRate, systolicBP, diastolicBP, oxygenLevel, bodyTemperature]);

  useEffect(() => {
    if (!userId || !monitoringActive) {
      if (monitorIntervalRef.current) {
        window.clearInterval(monitorIntervalRef.current);
      }
      return;
    }

    const tick = () => {
      const riskPercentage = getCurrentRisk(userId);
      const currentHistory = loadVitalsHistory(userId);
      const currentAlerts = loadAlertHistory(userId);
      const monitoring = monitorPatient({
        userId,
        previousHistory: currentHistory,
        previousAlerts: currentAlerts,
        riskPercentage,
        relatedGoal: activeGoalTitle,
      });
      if (!isMountedRef.current) return;
      setLiveRisk(riskPercentage);
      setVitalsHistory(monitoring.vitalsHistory);
      setAlertHistory(monitoring.alertHistory);
      setLiveVitals(monitoring.vitals);
      setLatestAlert(monitoring.latestAlert);
    };

    tick();
    monitorIntervalRef.current = window.setInterval(tick, 7000);

    return () => {
      if (monitorIntervalRef.current) {
        window.clearInterval(monitorIntervalRef.current);
      }
    };
  }, [userId, monitoringActive, activeGoalTitle]);

  async function generateInsight() {
    setAiInsightBusy(true);
    setError(null);
    try {
      const response = await getHealthInsight();
      setAiInsight(response.data.insight);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to generate AI insight");
    } finally {
      setAiInsightBusy(false);
    }
  }

  async function handleGenerateMonitoringReport() {
    setMonitoringBusy(true);
    setError(null);
    try {
      let currentRecord = {
        bmi: null,
        blood_glucose_level: null,
        hba1c_level: null,
        blood_pressure: null,
        overall_risk_score: null,
        overall_health_score: null,
      };

      // Try to get latest health record if available
      try {
        const latestHealthRecord = await getLatestHealthRecord();
        if (latestHealthRecord) {
          const recordData = latestHealthRecord.health_record || latestHealthRecord;
          const predictionData = latestHealthRecord.prediction || {};
          currentRecord = {
            bmi: recordData.bmi,
            blood_glucose_level: recordData.blood_glucose_level,
            hba1c_level: recordData.hba1c_level,
            blood_pressure: recordData.blood_pressure,
            overall_risk_score: predictionData.overall_risk_score,
            overall_health_score: predictionData.health_index?.score,
          };
        }
      } catch (err) {
        // No health records yet, which is okay - we can still generate a report
        console.log("No latest health record available, proceeding with empty baseline");
      }

      const report = await generateMonitoringReportApi(currentRecord);
      setMonitoringReport(report);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to generate monitoring report");
    } finally {
      setMonitoringBusy(false);
    }
  }

  return (
    <RequireAuth>
      <DashboardLayout
        title="Monitoring & Alerts"
        subtitle="Continuously monitor live vitals, evaluate risk-driven alerts, and turn changes into clear next-step guidance."
      >
        {error ? (
          <div className="mb-6 rounded border border-red-900/60 bg-red-950/40 p-3 text-sm text-red-200">{error}</div>
        ) : null}
        {savedMessage ? (
          <div className="mb-6 rounded border border-emerald-900/60 bg-emerald-950/30 p-3 text-sm text-emerald-200">{savedMessage}</div>
        ) : null}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5 text-slate-100 shadow-xl shadow-slate-950/20">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-lg font-semibold">Live Monitoring Dashboard</div>
                <div className="mt-1 text-sm text-slate-400">Vitals are refreshed every 5–10 seconds using the latest prediction and saved monitoring baseline.</div>
              </div>
              <button
                type="button"
                onClick={() => setMonitoringActive((prev) => !prev)}
                className={`rounded-full px-4 py-2 text-sm font-semibold ${monitoringActive ? "bg-emerald-500/10 text-emerald-200" : "bg-slate-800 text-slate-300"}`}
              >
                {monitoringActive ? "Monitoring Active" : "Monitoring Paused"}
              </button>
            </div>

            <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              <LiveMetricCard
                label="Heart Rate"
                value={liveVitals ? `${Math.round(liveVitals.heart_rate_bpm)} bpm` : "—"}
                trend={liveTrends.heart_rate_bpm}
                tone={trendTone(liveTrends.heart_rate_bpm, "goodWhenDown")}
              />
              <LiveMetricCard
                label="Blood Pressure"
                value={formatBloodPressure(liveVitals)}
                trend={liveTrends.blood_pressure}
                tone={trendTone(liveTrends.blood_pressure, "goodWhenDown")}
              />
              <LiveMetricCard
                label="Oxygen (SpO2)"
                value={liveVitals ? `${liveVitals.oxygen_level}%` : "—"}
                trend={liveTrends.oxygen_level}
                tone={trendTone(liveTrends.oxygen_level, "goodWhenUp")}
              />
              <LiveMetricCard
                label="Temperature"
                value={liveVitals ? `${liveVitals.body_temperature_c} °C` : "—"}
                trend={liveTrends.body_temperature_c}
                tone={trendTone(liveTrends.body_temperature_c, "goodWhenDown")}
              />
              <LiveMetricCard
                label="Prediction Risk"
                value={toRiskPercent(liveRisk)}
                trend={liveTrends.risk_percentage}
                tone={trendTone(liveTrends.risk_percentage, "goodWhenDown")}
              />
              <LiveMetricCard
                label="Monitoring Source"
                value={liveVitals?.source === "manual" ? "Manual baseline" : "Simulated"}
                trend="stable"
                tone="text-slate-400"
              />
            </div>

            <div className={`mt-6 rounded-2xl border p-5 ${levelClasses(latestAlert?.level || "NORMAL")}`}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.22em] opacity-80">Alert Panel</div>
                  <div className="mt-2 text-xl font-bold">{latestAlert?.level || "NORMAL"}</div>
                  <div className="mt-2 text-sm leading-6">{latestAlert?.message || "All vitals are currently within the safe monitoring range."}</div>
                </div>
                <div className="text-right text-xs opacity-80">
                  <div>{latestAlert ? new Date(latestAlert.timestamp).toLocaleTimeString() : "Live"}</div>
                  {latestAlert?.related_goal ? <div className="mt-1 max-w-[15rem]">{latestAlert.related_goal}</div> : null}
                </div>
              </div>

              <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
                {(latestAlert?.recommendation || ["Continue routine monitoring."]).map((item) => (
                  <div key={item} className="rounded-xl border border-white/10 bg-black/10 px-3 py-3 text-sm">
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-100">Alert History</div>
                  <div className="mt-1 text-xs text-slate-500">Duplicate alerts are suppressed unless the level changes or the condition gets worse.</div>
                </div>
                <div className="text-xs text-slate-500">{alertHistory.length} stored alert(s)</div>
              </div>
              <div className="mt-4 space-y-2">
                {alertHistory.length === 0 ? (
                  <div className="text-sm text-slate-400">No live alerts have been generated yet.</div>
                ) : (
                  [...alertHistory].slice(-5).reverse().map((alert) => (
                    <div key={alert.id} className={`rounded-xl border px-3 py-3 text-sm ${levelClasses(alert.level)}`}>
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-semibold">{alert.level}</span>
                        <span className="text-xs opacity-80">{new Date(alert.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <div className="mt-1">{alert.message}</div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5 text-slate-100 shadow-xl shadow-slate-950/20">
              <div className="font-semibold">Add a monitoring baseline</div>
              <div className="mt-1 text-sm text-slate-400">Manual values become the baseline for the live monitoring loop and are also saved as a device reading.</div>

              <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
                <Field label="Heart rate (bpm)">
                  <input type="number" className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2" value={heartRate} onChange={(e) => setHeartRate(Number(e.target.value))} />
                </Field>
                <Field label="Oxygen level (SpO2 %)">
                  <input type="number" className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2" value={oxygenLevel} onChange={(e) => setOxygenLevel(Number(e.target.value))} />
                </Field>
                <Field label="Systolic BP">
                  <input type="number" className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2" value={systolicBP} onChange={(e) => setSystolicBP(Number(e.target.value))} />
                </Field>
                <Field label="Diastolic BP">
                  <input type="number" className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2" value={diastolicBP} onChange={(e) => setDiastolicBP(Number(e.target.value))} />
                </Field>
                <Field label="Body temperature (°C)">
                  <input type="number" step="0.1" className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2" value={bodyTemperature} onChange={(e) => setBodyTemperature(Number(e.target.value))} />
                </Field>
                <Field label="Current Risk">
                  <div className="mt-1 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200">{toRiskPercent(liveRisk)}</div>
                </Field>
              </div>

              <div className="mt-4 flex items-center gap-3">
                <button
                  disabled={busy}
                  onClick={async () => {
                    if (!userId) return;
                    setBusy(true);
                    setError(null);
                    setSavedMessage(null);
                    try {
                      saveManualBaseline(userId, {
                        heart_rate_bpm: heartRate,
                        systolic_bp: systolicBP,
                        diastolic_bp: diastolicBP,
                        oxygen_level: oxygenLevel,
                        body_temperature_c: bodyTemperature,
                      });
                      await addDeviceReading({
                        recorded_at: new Date().toISOString(),
                        source: "manual",
                        heart_rate_bpm: heartRate,
                        steps: null,
                        sleep_minutes: null,
                        payload: {
                          blood_pressure: `${systolicBP}/${diastolicBP}`,
                          oxygen_level: oxygenLevel,
                          body_temperature_c: bodyTemperature,
                        },
                      });
                      setSavedMessage("Manual monitoring baseline saved. The live dashboard will use it on the next refresh cycle.");
                    } catch (e: any) {
                      setError(e?.response?.data?.detail || e?.message || "Failed to save monitoring baseline");
                    } finally {
                      setBusy(false);
                    }
                  }}
                  className="rounded bg-indigo-500 px-4 py-2 text-white disabled:opacity-50"
                >
                  {busy ? "Saving..." : "Save baseline"}
                </button>
                <button
                  onClick={() => refresh()}
                  className="rounded border border-slate-700 bg-slate-950 px-4 py-2"
                >
                  Refresh Data
                </button>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5 text-slate-100 shadow-xl shadow-slate-950/20">
              <div className="font-semibold">Connected suggestions</div>
              <div className="mt-1 text-sm text-slate-400">Alerts suggest actions and can reference your current prevention goal without changing task logic.</div>
              <div className="mt-4 space-y-2">
                {(latestAlert?.recommendation || ["Continue normal preventive care and monitor risk changes."]).map((item) => (
                  <div key={item} className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-3 text-sm text-slate-200">
                    {item}
                  </div>
                ))}
              </div>
              {activeGoalTitle ? (
                <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950 px-3 py-3 text-sm text-slate-300">
                  Related goal: {activeGoalTitle}
                </div>
              ) : null}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5 text-slate-100 shadow-xl shadow-slate-950/20 lg:col-span-2">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <div className="font-semibold">🔹 Health Monitoring Report</div>
                <div className="text-sm text-slate-400">Comprehensive analysis of your historical health trends, anomalies, and recommendations.</div>
              </div>
              <button
                onClick={handleGenerateMonitoringReport}
                disabled={monitoringBusy}
                className="rounded bg-green-600 px-4 py-2 text-white hover:bg-green-700 disabled:opacity-50"
              >
                {monitoringBusy ? "Generating..." : "Generate Report"}
              </button>
            </div>

            {monitoringReport ? (
              <div className="space-y-6">
                <div>
                  <h3 className="mb-3 font-semibold text-green-400">Trend Analysis</h3>
                  <div className="grid grid-cols-1 gap-2 md:grid-cols-2 lg:grid-cols-3">
                    {Object.entries(monitoringReport.trend_analysis || {}).map(([param, data]: [string, any]) => (
                      <div key={param} className="rounded border border-slate-700 bg-slate-950 p-3">
                        <div className="text-sm font-medium">{data.label || param.replace(/_/g, " ")}</div>
                        <div className="text-xs text-slate-400">
                          {data.trend} ({data.assessment})
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {monitoringReport.risk_change ? (
                  <div>
                    <h3 className="mb-3 font-semibold text-blue-400">Risk Change</h3>
                    <div className="rounded border border-slate-700 bg-slate-950 p-4">
                      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                        <InfoCell label="Previous Risk" value={`${monitoringReport.risk_change.previous_risk ?? "N/A"}%`} />
                        <InfoCell label="Current Risk" value={`${monitoringReport.risk_change.current_risk ?? "N/A"}%`} />
                        <InfoCell label="Change" value={`${monitoringReport.risk_change.change > 0 ? "+" : ""}${monitoringReport.risk_change.change ?? "N/A"}%`} />
                        <InfoCell label="Status" value={monitoringReport.risk_change.status} />
                      </div>
                    </div>
                  </div>
                ) : null}

                {monitoringReport.anomaly_detection?.length ? (
                  <div>
                    <h3 className="mb-3 font-semibold text-red-400">Anomaly Detection</h3>
                    <div className="space-y-2">
                      {monitoringReport.anomaly_detection.map((anomaly: any, index: number) => (
                        <div key={index} className="rounded border border-red-700 bg-red-950/20 p-3">
                          <div className="flex items-center justify-between gap-3">
                            <div className="font-medium">{anomaly.description}</div>
                            <div className="rounded bg-red-600 px-2 py-1 text-xs">{anomaly.severity}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}

                {monitoringReport.health_insights ? (
                  <div>
                    <h3 className="mb-3 font-semibold text-purple-400">Health Insights</h3>
                    <div className="rounded border border-slate-700 bg-slate-950 p-4 text-sm text-slate-200">
                      {monitoringReport.health_insights}
                    </div>
                  </div>
                ) : null}

                {monitoringReport.recommendations?.length ? (
                  <div>
                    <h3 className="mb-3 font-semibold text-cyan-400">Recommendations</h3>
                    <div className="space-y-2">
                      {monitoringReport.recommendations.map((rec: string, index: number) => (
                        <div key={index} className="rounded border border-slate-700 bg-slate-950 p-3 text-sm text-slate-200">
                          {index + 1}. {rec}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="rounded border border-slate-800 bg-slate-950 p-4 text-sm text-slate-400">
                Generate a report to analyze your longer-term health trends and monitoring signals.
              </div>
            )}
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5 text-slate-100 shadow-xl shadow-slate-950/20 lg:col-span-2">
            <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="text-lg font-semibold">Prediction History</div>
                <div className="text-sm text-slate-400">Use past predictions as the risk source for live monitoring and alerts.</div>
              </div>
            </div>
            <div className="space-y-3">
              {predictionHistory.length === 0 ? (
                <div className="rounded border border-slate-800 bg-slate-950 p-4 text-sm text-slate-400">No prediction history available yet.</div>
              ) : (
                predictionHistory.slice(0, 5).map((item, idx) => (
                  <div key={idx} className="rounded border border-slate-800 bg-slate-950 p-4 text-sm text-slate-200">
                    <div className="flex items-center justify-between gap-3">
                      <span>{new Date(item.created_at).toLocaleString()}</span>
                      <span className="font-semibold">Score {Math.round(item.overall_health_score)}</span>
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-3 text-slate-300 sm:grid-cols-3">
                      <div>Diabetes: {Math.round(item.diabetes_risk * 100)}%</div>
                      <div>Heart risk: {item.heart_risk_level}</div>
                      <div>BMI status: {item.bmi_status}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
            {predictionTrend.length ? (
              <div className="mt-6 rounded border border-slate-800 bg-slate-950 p-4 text-sm text-slate-200">
                <div className="font-medium">Recent trend</div>
                <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
                  {predictionTrend.map((point, idx) => (
                    <div key={idx} className="rounded border border-slate-800 bg-slate-900 p-3">
                      <div className="text-xs text-slate-400">{new Date(point.created_at).toLocaleDateString()}</div>
                      <div className="mt-2 text-lg font-semibold text-slate-100">{Math.round(point.overall_health_score)}</div>
                      <div className="mt-1 text-slate-300">Diabetes {Math.round(point.diabetes_risk * 100)}%</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </DashboardLayout>
    </RequireAuth>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm text-slate-300">
      <span className="font-medium">{label}</span>
      {children}
    </label>
  );
}

function LiveMetricCard({
  label,
  value,
  trend,
  tone,
}: {
  label: string;
  value: string;
  trend: TrendDirection;
  tone: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
      <div className="text-sm text-slate-400">{label}</div>
      <div className="mt-2 flex items-center justify-between gap-3">
        <div className="text-2xl font-semibold text-slate-100">{value}</div>
        <div className={`text-xl font-bold ${tone}`}>{trendArrow(trend)}</div>
      </div>
    </div>
  );
}

function InfoCell({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-sm text-slate-400">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}
