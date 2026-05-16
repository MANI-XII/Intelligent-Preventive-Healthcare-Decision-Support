import { useEffect, useRef, useState } from "react";
import DashboardLayout from "../../components/DashboardLayout";
import RequireAuth from "../../components/RequireAuth";
import { cancelAllRequests, getHealthInsight } from "../../services/api";

type LogItem = {
  id: number;
  created_at: string;
  category: string;
  value: any;
};

type RiskDriver = {
  factor: string;
  impact_percent: number;
};

type InsightAnalysis = {
  summary: string;
  key_risk_drivers: RiskDriver[];
  trend_insight: string;
  risk_interaction: string;
  behavioral_insight: string;
  recommendations: string[];
};

function fallbackAnalysis(items: LogItem[]): InsightAnalysis {
  if (!items.length) {
    return {
      summary:
        "Not enough data is available yet to generate deeper cross-source insights. Add a health record and a few behavior logs to unlock a fuller explanation.",
      key_risk_drivers: [],
      trend_insight:
        "Trend analysis will appear after more monitoring or prediction history is recorded.",
      risk_interaction:
        "Risk interaction analysis needs prediction and monitoring data to explain how conditions influence each other.",
      behavioral_insight:
        "Behavior insights will become more useful once activity, sleep, diet, or medication logs are added over multiple days.",
      recommendations: [
        "Add a recent health record to create a baseline.",
        "Log activity, sleep, or diet for a few consecutive days.",
        "Refresh this page after new records are added to generate a fuller insight summary.",
      ],
    };
  }

  return {
    summary:
      "Behavior data is available, but richer insights need prediction and monitoring records too. Your current logs still help the system connect daily habits with future health changes.",
    key_risk_drivers: [
      { factor: "Limited clinical baseline data", impact_percent: 40 },
      { factor: "Early-stage behavior-only tracking", impact_percent: 25 },
    ],
    trend_insight: "Behavior logs are present, but there is not yet enough linked health history to describe reliable time-based patterns.",
    risk_interaction: "Behavior changes can influence weight, glucose control, and cardiovascular strain, but prediction data is still needed to explain those links clearly.",
    behavioral_insight: "Continue adding structured behavior entries so the system can connect habits with measurable health outcomes.",
    recommendations: [
      "Add a current health record with glucose, HbA1c, BMI, and blood pressure details.",
      "Keep logging behavior consistently for several days in a row.",
      "Use Refresh Insights after adding new health or monitoring data.",
    ],
  };
}

export default function InsightsPage() {
  const [insightBusy, setInsightBusy] = useState(false);
  const [insightError, setInsightError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<InsightAnalysis | null>(null);
  const [formattedInsight, setFormattedInsight] = useState<string | null>(null);
  const isMountedRef = useRef(true);

  async function refresh() {
    if (!isMountedRef.current) return;

    setInsightBusy(true);
    setInsightError(null);

    const insightResult = await getHealthInsight()
      .then((value) => ({ status: "fulfilled" as const, value }))
      .catch((reason) => ({ status: "rejected" as const, reason }));

    if (!isMountedRef.current) return;

    if (insightResult.status === "fulfilled") {
      const nextAnalysis = insightResult.value?.analysis || fallbackAnalysis([]);
      setAnalysis(nextAnalysis);
      setFormattedInsight(insightResult.value?.insight || null);
      setInsightError(null);
    } else {
      setAnalysis(fallbackAnalysis([]));
      setFormattedInsight(null);
      setInsightError((insightResult.reason as any)?.response?.data?.detail || "Unable to generate AI insights right now.");
    }

    setInsightBusy(false);
  }

  useEffect(() => {
    isMountedRef.current = true;
    refresh();

    return () => {
      isMountedRef.current = false;
      cancelAllRequests();
    };
  }, []);

  const currentAnalysis = analysis || fallbackAnalysis([]);

  return (
    <RequireAuth>
      <DashboardLayout
        title="Insights"
        subtitle="Cross-source health intelligence that connects prediction results, monitoring trends, and behavior patterns into explainable next steps."
      >
        {insightError ? (
          <div className="mb-4 rounded border border-amber-900/60 bg-amber-950/30 p-3 text-sm text-amber-200">{insightError}</div>
        ) : null}

        <div className="mb-6 rounded-2xl border border-slate-800 bg-slate-900 p-5 text-slate-100">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-lg font-semibold">AI Health Insight Summary</div>
              <p className="mt-3 text-sm leading-6 text-slate-300">
                {insightBusy ? "Generating a multi-source explanation from your latest health, monitoring, and behavior data..." : currentAnalysis.summary}
              </p>
            </div>
            <button
              onClick={() => refresh()}
              disabled={insightBusy}
              className="rounded border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-slate-100 disabled:opacity-50"
            >
              {insightBusy ? "Refreshing..." : "Refresh Insights"}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <InsightCard title="Key Risk Drivers">
            {currentAnalysis.key_risk_drivers.length === 0 ? (
              <div className="text-sm text-slate-400">Risk drivers will appear once more clinical and monitoring data is available.</div>
            ) : (
              <div className="space-y-3">
                {currentAnalysis.key_risk_drivers.map((item) => (
                  <div key={item.factor} className="rounded-xl border border-slate-800 bg-slate-950 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-medium text-slate-100">{item.factor}</div>
                      <div className="rounded-full bg-rose-500/10 px-3 py-1 text-xs font-semibold text-rose-200">
                        {item.impact_percent}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </InsightCard>

          <InsightCard title="Trend Insight">
            <p className="text-sm leading-6 text-slate-300">{currentAnalysis.trend_insight}</p>
          </InsightCard>

          <InsightCard title="Risk Interaction">
            <p className="text-sm leading-6 text-slate-300">{currentAnalysis.risk_interaction}</p>
          </InsightCard>

          <InsightCard title="Behavioral Insight">
            <p className="text-sm leading-6 text-slate-300">{currentAnalysis.behavioral_insight}</p>
          </InsightCard>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <InsightCard title="Actionable Recommendations">
            <div className="space-y-3">
              {currentAnalysis.recommendations.map((item) => (
                <div key={item} className="rounded-xl border border-emerald-900/40 bg-emerald-950/10 p-3 text-sm text-emerald-100">
                  {item}
                </div>
              ))}
            </div>
          </InsightCard>

          <InsightCard title="AI Output Format">
            <pre className="whitespace-pre-wrap rounded-xl border border-slate-800 bg-slate-950 p-4 text-xs leading-6 text-slate-300">
              {formattedInsight || "The formatted insight output will appear here after the analysis is generated."}
            </pre>
          </InsightCard>
        </div>
      </DashboardLayout>
    </RequireAuth>
  );
}

function InsightCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 text-slate-100">
      <div className="font-semibold">{title}</div>
      <div className="mt-4">{children}</div>
    </div>
  );
}
