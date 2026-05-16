import { useEffect, useMemo, useState } from "react";
import DashboardLayout from "../../components/DashboardLayout";
import ExplainableChart from "../../components/ExplainableChart";
import RequireAuth from "../../components/RequireAuth";
import { useAuth } from "../../context/AuthContext";
import {
  defaultHealthInput,
  HealthInput,
  loadInput,
  loadLatestPrediction,
  PredictionResult,
  runSimulation,
} from "../../services/healthInput";
import { applySimulation } from "../../services/goalAutomation";

function formatPct(v: number) {
  return `${Math.round(v * 100)}%`;
}

function formatSignedPct(v: number) {
  const rounded = Math.round(v);
  return `${rounded > 0 ? "+" : ""}${rounded}%`;
}

function copyInput(input: HealthInput): HealthInput {
  return { ...input };
}

function buildComparison(original: PredictionResult, simulated: PredictionResult) {
  const originalRisk = original.overall_risk_score;
  const simulatedRisk = simulated.overall_risk_score;
  const riskDelta = simulatedRisk - originalRisk;
  const riskReduction = originalRisk === 0 ? 0 : ((originalRisk - simulatedRisk) / originalRisk) * 100;
  const healthDelta = simulated.health_index.score - original.health_index.score;

  return {
    riskDelta,
    riskReduction,
    healthDelta,
    summary:
      riskDelta < 0
        ? `Risk reduced by ${Math.round(Math.abs(riskReduction))}% after the simulated health changes.`
        : riskDelta > 0
          ? `Risk increased by ${Math.round(Math.abs(riskReduction))}% after the simulated health changes.`
          : "Overall risk stayed the same in this simulation.",
  };
}

export default function SimulatePage() {
  const { userId } = useAuth();
  const [originalInput, setOriginalInput] = useState<HealthInput>(defaultHealthInput);
  const [modifiedInput, setModifiedInput] = useState<HealthInput>(defaultHealthInput);
  const [originalResult, setOriginalResult] = useState<PredictionResult | null>(null);
  const [simulatedResult, setSimulatedResult] = useState<PredictionResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [applyBusy, setApplyBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) return;

    const sharedInput = loadInput(userId) ?? defaultHealthInput;
    const sharedPrediction = loadLatestPrediction(userId);

    setOriginalInput(copyInput(sharedInput));
    setModifiedInput(copyInput(sharedInput));
    setOriginalResult(sharedPrediction);
    setSimulatedResult(null);
    setError(null);
    setMessage(null);
  }, [userId]);

  const comparison = useMemo(() => {
    if (!originalResult || !simulatedResult) return null;
    return buildComparison(originalResult, simulatedResult);
  }, [originalResult, simulatedResult]);

  return (
    <RequireAuth>
      <DashboardLayout
        title="Simulation"
        subtitle="Use the same health input from Prediction, test changes safely, and apply them only when you are ready."
      >
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 text-slate-100">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-lg font-semibold">Simulation Input</div>
                <div className="mt-1 text-sm text-slate-400">
                  Prediction data is loaded automatically. Changes here are temporary until you click Apply Simulation.
                </div>
              </div>
              <div className="rounded-full bg-slate-950 px-3 py-1 text-sm text-slate-300">Shared Data</div>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="Gender">
                <select className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={modifiedInput.gender} onChange={(e) => setModifiedInput((prev) => ({ ...prev, gender: e.target.value as HealthInput["gender"] }))}>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </Field>
              <Field label="Age">
                <input type="number" className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={modifiedInput.age} onChange={(e) => setModifiedInput((prev) => ({ ...prev, age: Number(e.target.value) }))} />
              </Field>
              <Field label="BMI">
                <input type="number" step="0.1" className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={modifiedInput.bmi} onChange={(e) => setModifiedInput((prev) => ({ ...prev, bmi: Number(e.target.value) }))} />
              </Field>
              <Field label="Blood Glucose">
                <input type="number" className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={modifiedInput.blood_glucose_level} onChange={(e) => setModifiedInput((prev) => ({ ...prev, blood_glucose_level: Number(e.target.value) }))} />
              </Field>
              <Field label="HbA1c">
                <input type="number" step="0.1" className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={modifiedInput.hba1c_level} onChange={(e) => setModifiedInput((prev) => ({ ...prev, hba1c_level: Number(e.target.value) }))} />
              </Field>
              <Field label="Smoking">
                <select className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={modifiedInput.smoking_history} onChange={(e) => setModifiedInput((prev) => ({ ...prev, smoking_history: e.target.value as HealthInput["smoking_history"] }))}>
                  <option value="never">never</option>
                  <option value="former">former</option>
                  <option value="current">current</option>
                </select>
              </Field>
              <Field label="Activity Level">
                <select className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={modifiedInput.activity_level} onChange={(e) => setModifiedInput((prev) => ({ ...prev, activity_level: e.target.value as HealthInput["activity_level"] }))}>
                  <option value="low">low</option>
                  <option value="moderate">moderate</option>
                  <option value="high">high</option>
                </select>
              </Field>
              <Field label="Sleep Hours">
                <input type="number" step="0.5" min={0} max={24} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={modifiedInput.sleep_hours} onChange={(e) => setModifiedInput((prev) => ({ ...prev, sleep_hours: Number(e.target.value) }))} />
              </Field>
              <Field label="Stress Level">
                <select className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={modifiedInput.stress_level} onChange={(e) => setModifiedInput((prev) => ({ ...prev, stress_level: e.target.value as HealthInput["stress_level"] }))}>
                  <option value="low">low</option>
                  <option value="moderate">moderate</option>
                  <option value="high">high</option>
                </select>
              </Field>
              <Field label="Diet Type">
                <select className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={modifiedInput.diet_type} onChange={(e) => setModifiedInput((prev) => ({ ...prev, diet_type: e.target.value as HealthInput["diet_type"] }))}>
                  <option value="balanced">balanced</option>
                  <option value="low-sugar">low-sugar</option>
                  <option value="vegetarian">vegetarian</option>
                  <option value="high-carb">high-carb</option>
                  <option value="high-fat">high-fat</option>
                  <option value="other">other</option>
                </select>
              </Field>
              <Field label="Hypertension">
                <select className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={modifiedInput.hypertension} onChange={(e) => setModifiedInput((prev) => ({ ...prev, hypertension: Number(e.target.value) }))}>
                  <option value={0}>0</option>
                  <option value={1}>1</option>
                </select>
              </Field>
              <Field label="Heart Disease">
                <select className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={modifiedInput.heart_disease} onChange={(e) => setModifiedInput((prev) => ({ ...prev, heart_disease: Number(e.target.value) }))}>
                  <option value={0}>0</option>
                  <option value={1}>1</option>
                </select>
              </Field>
            </div>

            {error ? <div className="mt-6 rounded border border-red-900/60 bg-red-950/40 p-3 text-sm text-red-200">{error}</div> : null}
            {message ? <div className="mt-6 rounded border border-emerald-900/60 bg-emerald-950/30 p-3 text-sm text-emerald-200">{message}</div> : null}

            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <button
                disabled={busy || !originalResult}
                onClick={async () => {
                  setBusy(true);
                  setError(null);
                  setMessage(null);
                  try {
                    const result = await runSimulation(modifiedInput);
                    setSimulatedResult(result);
                  } catch (e) {
                    const err = e as { response?: { data?: { detail?: string } }; message?: string };
                    setError(err.response?.data?.detail || err.message || "Simulation failed");
                  } finally {
                    setBusy(false);
                  }
                }}
                className="inline-flex w-full items-center justify-center rounded bg-indigo-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-600 disabled:opacity-50"
              >
                {busy ? "Simulating..." : "Run Simulation"}
              </button>
              <button
                type="button"
                disabled={applyBusy || !simulatedResult}
                onClick={async () => {
                  if (!simulatedResult) return;
                  setApplyBusy(true);
                  setError(null);
                  try {
                    const goalWorkflow = await applySimulation(userId, modifiedInput, simulatedResult);
                    setOriginalInput(copyInput(modifiedInput));
                    setOriginalResult(simulatedResult);
                    setSimulatedResult(null);
                    if (goalWorkflow.action === "update") {
                      setMessage("Simulation applied and the linked goal was updated because the new risk changed significantly.");
                    } else if (goalWorkflow.action === "create") {
                      setMessage("Simulation applied and a new linked goal was created from the updated prediction.");
                    } else {
                      setMessage("Simulation applied. Prediction, Simulation, and the current goal now share the updated health input.");
                    }
                  } finally {
                    setApplyBusy(false);
                  }
                }}
                className="inline-flex w-full items-center justify-center rounded border border-emerald-700 bg-emerald-950/40 px-5 py-3 text-sm font-semibold text-emerald-100 transition hover:border-emerald-500 disabled:opacity-50"
              >
                {applyBusy ? "Applying..." : "Apply Simulation → Update Goal"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setModifiedInput(copyInput(originalInput));
                  setSimulatedResult(null);
                  setError(null);
                  setMessage("Simulation changes discarded. Original prediction data is unchanged.");
                }}
                className="inline-flex w-full items-center justify-center rounded border border-slate-700 bg-slate-900 px-5 py-3 text-sm font-semibold text-slate-100 transition hover:border-slate-600"
              >
                Reset Changes
              </button>
            </div>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 text-slate-100">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-lg font-semibold">Comparison Output</div>
                <div className="mt-1 text-sm text-slate-400">Compare the saved prediction with your simulated changes.</div>
              </div>
              <div className="rounded-full bg-slate-950 px-3 py-1 text-sm text-slate-300">Before / After</div>
            </div>

            {!originalResult ? (
              <div className="mt-6 rounded-xl border border-dashed border-slate-700 bg-slate-950/40 px-4 py-8 text-center text-sm text-slate-400">
                Run a prediction first. Simulation uses the shared prediction data from the Prediction page.
              </div>
            ) : !simulatedResult ? (
              <div className="mt-6 text-sm text-slate-300">Update the shared inputs on the left, then run the simulation to compare results.</div>
            ) : (
              <>
                <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <MetricCard label="Before Risk" value={`${Math.round(originalResult.overall_risk_score)}%`} helper={originalResult.overall_risk_level} />
                  <MetricCard label="After Risk" value={`${Math.round(simulatedResult.overall_risk_score)}%`} helper={simulatedResult.overall_risk_level} />
                  <MetricCard label="Before Health Index" value={`${Math.round(originalResult.health_index.score)}`} helper={originalResult.health_category} />
                  <MetricCard label="After Health Index" value={`${Math.round(simulatedResult.health_index.score)}`} helper={simulatedResult.health_category} />
                </div>

                {comparison ? (
                  <div className="mt-4 rounded-lg border border-indigo-700/40 bg-indigo-950/20 p-4">
                    <div className="text-sm font-semibold text-indigo-100">Simulation Summary</div>
                    <div className="mt-2 text-sm text-indigo-200">{comparison.summary}</div>
                    <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
                      <MetricCard label="Overall Risk Change" value={formatSignedPct(comparison.riskDelta)} helper="Negative is better" compact />
                      <MetricCard label="Risk Reduction" value={`${Math.round(comparison.riskReduction)}%`} helper="From saved prediction" compact />
                      <MetricCard label="Health Index Change" value={formatSignedPct(comparison.healthDelta)} helper="Positive is better" compact />
                    </div>
                  </div>
                ) : null}

                <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <MetricCard
                    label="Before Diabetes"
                    value={formatPct(originalResult.disease_scores?.diabetes?.probability ?? 0)}
                    helper={originalResult.disease_scores?.diabetes?.risk_level ?? "N/A"}
                  />
                  <MetricCard
                    label="After Diabetes"
                    value={formatPct(simulatedResult.disease_scores?.diabetes?.probability ?? 0)}
                    helper={simulatedResult.disease_scores?.diabetes?.risk_level ?? "N/A"}
                  />
                  <MetricCard
                    label="Difference"
                    value={formatSignedPct(((simulatedResult.disease_scores?.diabetes?.probability ?? 0) - (originalResult.disease_scores?.diabetes?.probability ?? 0)) * 100)}
                    helper="Diabetes risk delta"
                  />
                </div>

                <div className="mt-6 rounded-lg border border-slate-800 bg-slate-950 p-4">
                  <div className="font-semibold text-slate-100">Simulated Explainability</div>
                  <div className="mt-3 text-sm text-slate-300">Review what changed in the simulated prediction.</div>
                  <ExplainableChart explanations={simulatedResult.explanations} />
                </div>
              </>
            )}
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

function MetricCard({
  label,
  value,
  helper,
  compact = false,
}: {
  label: string;
  value: string;
  helper: string;
  compact?: boolean;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
      <div className="text-sm text-slate-400">{label}</div>
      <div className={`mt-2 font-semibold text-slate-100 ${compact ? "text-xl" : "text-2xl"}`}>{value}</div>
      <div className="mt-1 text-xs text-slate-400">{helper}</div>
    </div>
  );
}
