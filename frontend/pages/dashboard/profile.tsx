import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/router";
import {
  UserIcon,
  CakeIcon,
  LanguageIcon,
  ScaleIcon,
  HeartIcon,
  MoonIcon,
  BoltIcon,
  FireIcon,
  BriefcaseIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ArrowsRightLeftIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  InboxArrowDownIcon,
} from "@heroicons/react/24/outline";
import DashboardLayout from "../../components/DashboardLayout";
import RequireAuth from "../../components/RequireAuth";
import { useAuth } from "../../context/AuthContext";
import { loadInput } from "../../services/healthInput";
import {
  APP_DATA_CHANGED_EVENT,
  createHealthRecord,
  getHealthScore,
  getLatestHealthRecord,
  getPredictionTrend,
  getProfile,
  updateProfile,
  cancelAllRequests,
} from "../../services/api";

type PredictionTrendPoint = {
  created_at: string;
  diabetes_risk: number;
  heart_disease_risk: number;
  hypertension_risk: number;
  overall_health_score: number;
};

export default function ProfilePage() {
  const router = useRouter();
  const { userId } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isMountedRef = useRef(true);
  const latestLoadTokenRef = useRef(0);

  const [fullName, setFullName] = useState("");
  const [heightCm, setHeightCm] = useState<string>("");
  const [weightKg, setWeightKg] = useState<string>("");
  const [locale, setLocale] = useState<string>("en");
  const [latestRecord, setLatestRecord] = useState<any>(null);
  const [healthScore, setHealthScore] = useState<number | null>(null);
  const [predictionTrend, setPredictionTrend] = useState<PredictionTrendPoint[]>([]);

  const [gender, setGender] = useState<"Male" | "Female" | "Other">("Male");
  const [age, setAge] = useState<string>("30");
  const [bmi, setBmi] = useState<string>("");
  const [bloodGlucose, setBloodGlucose] = useState<string>("");
  const [hba1c, setHba1c] = useState<string>("");
  const [smoking, setSmoking] = useState<"never" | "former" | "current">("never");
  const [hypertension, setHypertension] = useState<number>(0);
  const [heartDisease, setHeartDisease] = useState<number>(0);
  const [activityLevel, setActivityLevel] = useState<"low" | "moderate" | "high">("moderate");
  const [sleepHours, setSleepHours] = useState<string>("7");
  const [stressLevel, setStressLevel] = useState<"low" | "moderate" | "high">("moderate");
  const [dietType, setDietType] = useState<"balanced" | "high-carb" | "high-fat" | "low-sugar" | "vegetarian" | "other">("balanced");
  const [workType, setWorkType] = useState<"sedentary" | "active" | "mixed">("mixed");
  const [bloodPressure, setBloodPressure] = useState<string>("");
  const [notes, setNotes] = useState<string>("");

  function applyPredictionFallback() {
    const savedInput = loadInput(userId);
    if (!savedInput) return false;

    setBmi(String(savedInput.bmi ?? ""));
    setBloodGlucose(String(savedInput.blood_glucose_level ?? ""));
    setHba1c(String(savedInput.hba1c_level ?? ""));
    setBloodPressure(savedInput.blood_pressure || "");
    return true;
  }

  async function load(options?: { silent?: boolean }) {
    if (!isMountedRef.current) return;
    const loadToken = Date.now();
    latestLoadTokenRef.current = loadToken;
    try {
      const [profileRes, scoreRes, trendRes] = await Promise.allSettled([
        getProfile(),
        getHealthScore(),
        getPredictionTrend(),
      ]);

      if (!isMountedRef.current || latestLoadTokenRef.current !== loadToken) return;

      if (profileRes.status === "fulfilled") {
        const res = profileRes.value;
        setProfile(res);
        setFullName(res?.full_name || "");
        setHeightCm(res?.height_cm ? String(res.height_cm) : "");
        setWeightKg(res?.weight_kg ? String(res.weight_kg) : "");
        setLocale(res?.locale || "en");
      }

      if (scoreRes.status === "fulfilled") {
        setHealthScore(scoreRes.value?.score ?? scoreRes.value?.data?.score ?? null);
      }

      if (trendRes.status === "fulfilled") {
        setPredictionTrend(trendRes.value?.trend || []);
      }

      try {
        const recordRes = await getLatestHealthRecord();
        if (!isMountedRef.current || latestLoadTokenRef.current !== loadToken) return;

        const record = recordRes?.health_record;
        if (record) {
          setLatestRecord(record);
          setGender(record.gender || "Male");
          setAge(String(record.age ?? 30));
          setBmi(String(record.bmi ?? ""));
          setBloodGlucose(String(record.blood_glucose_level ?? ""));
          setHba1c(String(record.hba1c_level ?? ""));
          setSmoking(record.smoking_history || "never");
          setHypertension(record.hypertension ?? 0);
          setHeartDisease(record.heart_disease ?? 0);
          setActivityLevel(record.activity_level || "moderate");
          setSleepHours(String(record.sleep_hours ?? "7"));
          setStressLevel(record.stress_level || "moderate");
          setDietType(record.diet_type || "balanced");
          setWorkType(record.work_type || "mixed");
          setBloodPressure(record.blood_pressure || "");
          setNotes(record.notes || "");
        } else {
          setLatestRecord(null);
          applyPredictionFallback();
        }
      } catch {
        if (isMountedRef.current && latestLoadTokenRef.current === loadToken) {
          setLatestRecord(null);
          applyPredictionFallback();
        }
      }
    } catch (e: any) {
      if (isMountedRef.current && !options?.silent) {
        console.error("Failed to load profile:", e);
      }
    }
  }

  async function saveHealthRecord() {
    if (!isMountedRef.current) return;
    setBusy(true);
    setError(null);
    try {
      const payload = {
        gender,
        age: Number(age) || 0,
        bmi: Number(bmi) || 0,
        blood_glucose_level: Number(bloodGlucose) || 0,
        hba1c_level: Number(hba1c) || 0,
        smoking_history: smoking,
        hypertension,
        heart_disease: heartDisease,
        activity_level: activityLevel,
        sleep_hours: Number(sleepHours) || 0,
        stress_level: stressLevel,
        diet_type: dietType,
        work_type: workType,
        blood_pressure: bloodPressure || undefined,
        notes: notes || undefined,
      };

      await createHealthRecord(payload);
      if (isMountedRef.current) {
        await load();
      }
    } catch (e: any) {
      if (isMountedRef.current) {
        setError(e?.response?.data?.detail || e?.message || "Failed to save health record");
      }
    } finally {
      if (isMountedRef.current) {
        setBusy(false);
      }
    }
  }

  useEffect(() => {
    isMountedRef.current = true;
    load();

    const handleAppDataChanged = () => {
      if (document.visibilityState === "visible") {
        load({ silent: true });
      }
    };

    const handleFocus = () => {
      load({ silent: true });
    };

    window.addEventListener(APP_DATA_CHANGED_EVENT, handleAppDataChanged as EventListener);
    window.addEventListener("focus", handleFocus);
    document.addEventListener("visibilitychange", handleFocus);

    return () => {
      isMountedRef.current = false;
      window.removeEventListener(APP_DATA_CHANGED_EVENT, handleAppDataChanged as EventListener);
      window.removeEventListener("focus", handleFocus);
      document.removeEventListener("visibilitychange", handleFocus);
      cancelAllRequests();
    };
  }, []);

  const displayName = fullName || "Profile not set";
  const summaryAge = age || "—";
  const summaryHeight = heightCm || "—";
  const summaryWeight = weightKg || "—";

  const scoreTone = useMemo(() => {
    if (healthScore == null) return "text-slate-300 border-slate-700 bg-slate-900";
    if (healthScore >= 75) return "text-emerald-200 border-emerald-700/40 bg-emerald-950/20";
    if (healthScore >= 50) return "text-amber-200 border-amber-700/40 bg-amber-950/20";
    return "text-rose-200 border-rose-700/40 bg-rose-950/20";
  }, [healthScore]);

  const scoreLabel = useMemo(() => {
    if (healthScore == null) return "Unavailable";
    if (healthScore >= 75) return "Good";
    if (healthScore >= 50) return "Moderate";
    return "Needs Attention";
  }, [healthScore]);

  const metricTone = (value: number | null, normalMax: number, warnMax: number) => {
    if (value == null || Number.isNaN(value)) return "border-slate-700 bg-slate-950/70 text-slate-300";
    if (value <= normalMax) return "border-emerald-700/40 bg-emerald-950/20 text-emerald-200";
    if (value <= warnMax) return "border-amber-700/40 bg-amber-950/20 text-amber-200";
    return "border-rose-700/40 bg-rose-950/20 text-rose-200";
  };

  const healthSummary = useMemo(() => {
    const glucoseValue = Number(bloodGlucose);
    const bmiValue = Number(bmi);
    const score = healthScore ?? latestRecord?.prediction?.overall_health_score ?? null;

    let riskLevel = "Low";
    if ((score != null && score < 5) || glucoseValue >= 180 || bmiValue >= 32) {
      riskLevel = "High";
    } else if ((score != null && score < 7.5) || glucoseValue >= 140 || bmiValue >= 25) {
      riskLevel = "Moderate";
    }

    let keyIssue = "No major issue detected";
    if (glucoseValue >= 180) keyIssue = "High Glucose";
    else if (Number(hba1c) >= 6.5) keyIssue = "Elevated HbA1c";
    else if (bmiValue >= 30) keyIssue = "High BMI";
    else if (bloodPressure && /^(\d+)\/(\d+)$/.test(bloodPressure)) {
      const match = bloodPressure.match(/^(\d+)\/(\d+)$/);
      if (match) {
        const systolic = Number(match[1]);
        const diastolic = Number(match[2]);
        if (systolic >= 140 || diastolic >= 90) keyIssue = "High Blood Pressure";
      }
    }

    let trend = "Stable";
    if (predictionTrend.length >= 2) {
      const first = predictionTrend[0]?.overall_health_score ?? 0;
      const last = predictionTrend[predictionTrend.length - 1]?.overall_health_score ?? 0;
      if (last > first + 2) trend = "Improving";
      else if (last < first - 2) trend = "Worsening";
    }

    return { riskLevel, keyIssue, trend };
  }, [bloodGlucose, bmi, hba1c, bloodPressure, healthScore, latestRecord, predictionTrend]);

  return (
    <RequireAuth>
      <DashboardLayout title="Profile" subtitle="Manage your profile, health metrics, and lifestyle details in one organized view.">
        {error ? (
          <div className="mb-6 rounded-2xl border border-red-900/60 bg-red-950/40 p-4 text-sm text-red-200">
            {error}
          </div>
        ) : null}

        <div className="space-y-6">
          <SectionCard className="overflow-hidden">
            <div className="grid gap-5 lg:grid-cols-[1.3fr_0.7fr]">
              <div className="space-y-4">
                <div>
                  <div className="flex items-center gap-2 text-2xl font-semibold text-slate-100">
                    <UserIcon className="h-6 w-6 text-cyan-300" />
                    <span>{displayName}</span>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-4 text-sm text-slate-300">
                    <span className="flex items-center gap-2">
                      <UserIcon className="h-4 w-4 text-slate-400" />
                      {gender} | {summaryAge} yrs
                    </span>
                    <span className="flex items-center gap-2">
                      <ArrowsRightLeftIcon className="h-4 w-4 text-slate-400" />
                      {summaryHeight} cm
                    </span>
                    <span className="flex items-center gap-2">
                      <ScaleIcon className="h-4 w-4 text-slate-400" />
                      {summaryWeight} kg
                    </span>
                  </div>
                </div>
                <div className="grid gap-3 sm:grid-cols-3">
                  <SummaryMiniCard label="Profile Owner" value={displayName} icon={<UserIcon className="h-5 w-5" />} />
                  <SummaryMiniCard label="Health Record" value={latestRecord ? "Available" : "Not Saved"} icon={<InboxArrowDownIcon className="h-5 w-5" />} />
                  <SummaryMiniCard label="Trend" value={healthSummary.trend} icon={<ArrowPathIcon className="h-5 w-5" />} />
                </div>
              </div>
              <div className={`rounded-3xl border p-5 shadow-inner transition ${scoreTone}`}>
                <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em]">
                  <HeartIcon className="h-5 w-5" />
                  Health Score
                </div>
                <div className="mt-5 text-5xl font-bold">{healthScore ?? "—"}</div>
                <div className="mt-2 text-sm">{scoreLabel}</div>
              </div>
            </div>
            </SectionCard>

          <div className="grid gap-6 xl:grid-cols-2">
            <SectionCard title="Personal Details" subtitle="Basic identity and language preferences.">
              <FieldGrid>
                <FieldShell label="Full Name" icon={<UserIcon className="h-4 w-4" />}>
                  <input
                    className="field-input"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </FieldShell>
                <FieldShell label="Age" icon={<CakeIcon className="h-4 w-4" />}>
                  <input
                    type="number"
                    min={0}
                    className="field-input"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                  />
                </FieldShell>
                <FieldShell label="Gender" icon={<UserIcon className="h-4 w-4" />}>
                  <select className="field-input" value={gender} onChange={(e) => setGender(e.target.value as "Male" | "Female" | "Other")}>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </FieldShell>
                <FieldShell label="Language" icon={<LanguageIcon className="h-4 w-4" />}>
                  <select className="field-input" value={locale} onChange={(e) => setLocale(e.target.value)}>
                    <option value="en">English</option>
                    <option value="hi">Hindi (MVP label)</option>
                    <option value="te">Telugu (MVP label)</option>
                  </select>
                </FieldShell>
              </FieldGrid>
            </SectionCard>

            <SectionCard title="Health Metrics" subtitle="Core preventive health numbers with visual status cues.">
              <FieldGrid>
                <FieldShell label="BMI" icon={<ScaleIcon className="h-4 w-4" />} tone={metricTone(Number(bmi), 24.9, 29.9)}>
                  <input type="number" readOnly className="field-input cursor-not-allowed opacity-80" value={bmi} />
                </FieldShell>
                <FieldShell label="Blood Glucose" icon={<BoltIcon className="h-4 w-4" />} tone={metricTone(Number(bloodGlucose), 110, 140)}>
                  <input type="number" readOnly className="field-input cursor-not-allowed opacity-80" value={bloodGlucose} />
                </FieldShell>
                <FieldShell label="HbA1c" icon={<FireIcon className="h-4 w-4" />} tone={metricTone(Number(hba1c), 5.6, 6.4)}>
                  <input type="number" readOnly className="field-input cursor-not-allowed opacity-80" value={hba1c} />
                </FieldShell>
                <FieldShell
                  label="Blood Pressure"
                  icon={<HeartIcon className="h-4 w-4" />}
                  tone={bloodPressure ? "border-rose-700/20 bg-slate-950/80 text-slate-100" : "border-slate-700 bg-slate-950/70 text-slate-300"}
                >
                  <input type="text" readOnly placeholder="e.g. 130/85" className="field-input cursor-not-allowed opacity-80" value={bloodPressure} />
                </FieldShell>
              </FieldGrid>
              <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-3 text-sm text-slate-400">
                BMI, blood glucose, HbA1c, and blood pressure are pulled from your latest Prediction entry. Use the Prediction page to change them.
              </div>
              <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-400">
                <LegendPill color="bg-emerald-400" label="Normal" />
                <LegendPill color="bg-amber-400" label="Warning" />
                <LegendPill color="bg-rose-400" label="High" />
              </div>
            </SectionCard>
          </div>

          <div className="grid gap-6 xl:grid-cols-2">
            <SectionCard title="Lifestyle & Behavior" subtitle="Daily habits that influence your preventive health outlook.">
              <FieldGrid>
                <FieldShell label="Height (cm)" icon={<ArrowsRightLeftIcon className="h-4 w-4" />}>
                  <input type="number" className="field-input" value={heightCm} onChange={(e) => setHeightCm(e.target.value)} />
                </FieldShell>
                <FieldShell label="Weight (kg)" icon={<ScaleIcon className="h-4 w-4" />}>
                  <input type="number" className="field-input" value={weightKg} onChange={(e) => setWeightKg(e.target.value)} />
                </FieldShell>
                <FieldShell label="Activity Level" icon={<BoltIcon className="h-4 w-4" />}>
                  <select className="field-input" value={activityLevel} onChange={(e) => setActivityLevel(e.target.value as "low" | "moderate" | "high")}>
                    <option value="low">low</option>
                    <option value="moderate">moderate</option>
                    <option value="high">high</option>
                  </select>
                </FieldShell>
                <FieldShell label="Sleep Hours" icon={<MoonIcon className="h-4 w-4" />}>
                  <input type="number" min={0} max={24} step="0.5" className="field-input" value={sleepHours} onChange={(e) => setSleepHours(e.target.value)} />
                </FieldShell>
                <FieldShell label="Smoking" icon={<FireIcon className="h-4 w-4" />}>
                  <select className="field-input" value={smoking} onChange={(e) => setSmoking(e.target.value as "never" | "former" | "current")}>
                    <option value="never">never</option>
                    <option value="former">former</option>
                    <option value="current">current</option>
                  </select>
                </FieldShell>
                <FieldShell label="Stress Level" icon={<ExclamationTriangleIcon className="h-4 w-4" />}>
                  <select className="field-input" value={stressLevel} onChange={(e) => setStressLevel(e.target.value as "low" | "moderate" | "high")}>
                    <option value="low">low</option>
                    <option value="moderate">moderate</option>
                    <option value="high">high</option>
                  </select>
                </FieldShell>
                <FieldShell label="Diet Type" icon={<CheckCircleIcon className="h-4 w-4" />}>
                  <select className="field-input" value={dietType} onChange={(e) => setDietType(e.target.value as "balanced" | "high-carb" | "high-fat" | "low-sugar" | "vegetarian" | "other")}>
                    <option value="balanced">balanced</option>
                    <option value="low-sugar">low-sugar</option>
                    <option value="vegetarian">vegetarian</option>
                    <option value="high-carb">high-carb</option>
                    <option value="high-fat">high-fat</option>
                    <option value="other">other</option>
                  </select>
                </FieldShell>
                <FieldShell label="Work Type" icon={<BriefcaseIcon className="h-4 w-4" />}>
                  <select className="field-input" value={workType} onChange={(e) => setWorkType(e.target.value as "sedentary" | "active" | "mixed")}>
                    <option value="sedentary">sedentary</option>
                    <option value="mixed">mixed</option>
                    <option value="active">active</option>
                  </select>
                </FieldShell>
              </FieldGrid>
            </SectionCard>

            <SectionCard title="Medical Conditions" subtitle="Known health conditions and notes for your record.">
              <FieldGrid>
                <FieldShell label="Hypertension" icon={<HeartIcon className="h-4 w-4" />}>
                  <select className="field-input" value={hypertension} onChange={(e) => setHypertension(Number(e.target.value))}>
                    <option value={0}>0</option>
                    <option value={1}>1</option>
                  </select>
                </FieldShell>
                <FieldShell label="Heart Disease" icon={<HeartIcon className="h-4 w-4" />}>
                  <select className="field-input" value={heartDisease} onChange={(e) => setHeartDisease(Number(e.target.value))}>
                    <option value={0}>0</option>
                    <option value={1}>1</option>
                  </select>
                </FieldShell>
                <FieldShell label="Notes" icon={<InboxArrowDownIcon className="h-4 w-4" />} className="md:col-span-2">
                  <textarea rows={4} className="field-input min-h-[112px]" value={notes} onChange={(e) => setNotes(e.target.value)} />
                </FieldShell>
              </FieldGrid>
            </SectionCard>
          </div>

          <SectionCard title="Health Summary" subtitle="Quick interpretation of your current profile and latest saved trend.">
            <div className="grid gap-4 md:grid-cols-3">
              <SummaryStat
                icon={<ChartIcon />}
                label="Risk Level"
                value={healthSummary.riskLevel}
                tone={healthSummary.riskLevel === "Low" ? "emerald" : healthSummary.riskLevel === "Moderate" ? "amber" : "rose"}
              />
              <SummaryStat
                icon={<ExclamationTriangleIcon className="h-5 w-5" />}
                label="Key Issue"
                value={healthSummary.keyIssue}
                tone={healthSummary.keyIssue === "No major issue detected" ? "emerald" : "amber"}
              />
              <SummaryStat
                icon={healthSummary.trend === "Improving" ? <ArrowTrendingUpIcon className="h-5 w-5" /> : healthSummary.trend === "Worsening" ? <ArrowTrendingDownIcon className="h-5 w-5" /> : <ArrowPathIcon className="h-5 w-5" />}
                label="Trend"
                value={healthSummary.trend}
                tone={healthSummary.trend === "Improving" ? "emerald" : healthSummary.trend === "Worsening" ? "rose" : "slate"}
              />
            </div>
          </SectionCard>

          <SectionCard>
            <div className="flex flex-wrap items-center gap-3">
              <button
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  setError(null);
                  try {
                    const res = await updateProfile({
                      full_name: fullName || null,
                      height_cm: heightCm ? Number(heightCm) : null,
                      weight_kg: weightKg ? Number(weightKg) : null,
                      locale,
                    });
                    setProfile(res);
                    await load();
                  } catch (e: any) {
                    setError(e?.response?.data?.detail || e?.message || "Failed to save profile");
                  } finally {
                    setBusy(false);
                  }
                }}
                className="inline-flex items-center gap-2 rounded-2xl bg-indigo-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-400 disabled:opacity-50"
              >
                <InboxArrowDownIcon className="h-5 w-5" />
                {busy ? "Saving..." : "Save Profile"}
              </button>
              <button
                disabled={busy}
                onClick={saveHealthRecord}
                className="inline-flex items-center gap-2 rounded-2xl bg-emerald-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-400 disabled:opacity-50"
              >
                <InboxArrowDownIcon className="h-5 w-5" />
                {busy ? "Saving..." : "Save Health Record"}
              </button>
              <button
                onClick={() => {
                  router.push("/dashboard/predict#clinical-metrics");
                }}
                className="inline-flex items-center gap-2 rounded-2xl border border-slate-700 bg-slate-950 px-5 py-3 text-sm font-semibold text-slate-100 transition hover:border-slate-500 hover:bg-slate-800"
              >
                <ArrowPathIcon className="h-5 w-5" />
                Update Data
              </button>
            </div>
          </SectionCard>
        </div>
      </DashboardLayout>
      <style jsx>{`
        .field-input {
          width: 100%;
          border-radius: 1rem;
          border: 1px solid rgb(51 65 85);
          background: rgb(2 6 23);
          padding: 0.75rem 0.95rem;
          color: rgb(241 245 249);
          transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
        }
        .field-input:hover {
          border-color: rgb(100 116 139);
        }
        .field-input:focus {
          outline: none;
          border-color: rgb(99 102 241);
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.18);
        }
      `}</style>
    </RequireAuth>
  );
}

function SectionCard({
  title,
  subtitle,
  children,
  className = "",
}: {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-[2rem] border border-slate-800 bg-slate-900/90 p-6 shadow-xl shadow-slate-950/10 transition hover:border-slate-700 ${className}`}>
      {title ? (
        <div className="mb-5">
          <h2 className="text-xl font-semibold text-slate-100">{title}</h2>
          {subtitle ? <p className="mt-1 text-sm leading-6 text-slate-400">{subtitle}</p> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}

function FieldGrid({ children }: { children: React.ReactNode }) {
  return <div className="grid grid-cols-1 gap-4 md:grid-cols-2">{children}</div>;
}

function FieldShell({
  label,
  icon,
  children,
  tone = "border-slate-800 bg-slate-950/40 text-slate-200",
  className = "",
}: {
  label: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  tone?: string;
  className?: string;
}) {
  return (
    <div className={`rounded-2xl border p-4 transition hover:-translate-y-0.5 hover:border-slate-700 ${tone} ${className}`}>
      <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-300">
        <span className="text-slate-400">{icon}</span>
        <span>{label}</span>
      </div>
      {children}
    </div>
  );
}

function SummaryMiniCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
        <span className="text-slate-500">{icon}</span>
        <span>{label}</span>
      </div>
      <div className="mt-3 text-sm font-medium text-slate-100">{value}</div>
    </div>
  );
}

function SummaryStat({
  icon,
  label,
  value,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  tone: "emerald" | "amber" | "rose" | "slate";
}) {
  const toneMap = {
    emerald: "border-emerald-700/40 bg-emerald-950/20 text-emerald-100",
    amber: "border-amber-700/40 bg-amber-950/20 text-amber-100",
    rose: "border-rose-700/40 bg-rose-950/20 text-rose-100",
    slate: "border-slate-700/60 bg-slate-950/70 text-slate-100",
  } as const;

  return (
    <div className={`rounded-3xl border p-5 ${toneMap[tone]}`}>
      <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] opacity-90">
        {icon}
        <span>{label}</span>
      </div>
      <div className="mt-4 text-2xl font-bold">{value}</div>
    </div>
  );
}

function LegendPill({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-950/80 px-3 py-1">
      <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
      <span>{label}</span>
    </span>
  );
}

function ChartIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19V5" />
      <path d="M10 19V10" />
      <path d="M16 19v-6" />
      <path d="M22 19V8" />
    </svg>
  );
}
