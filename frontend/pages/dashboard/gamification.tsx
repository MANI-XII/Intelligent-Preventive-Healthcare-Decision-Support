import { useEffect, useState, useRef } from "react";
import DashboardLayout from "../../components/DashboardLayout";
import RequireAuth from "../../components/RequireAuth";
import { getGamification, cancelAllRequests } from "../../services/api";

export default function GamificationPage() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;

    getGamification()
      .then((res) => {
        if (isMountedRef.current) {
          setData(res?.data || null);
        }
      })
      .catch((e) => {
        if (isMountedRef.current) {
          setError(e?.message || "Failed to load rewards");
        }
      });

    return () => {
      isMountedRef.current = false;
      cancelAllRequests();
    };
  }, []);

  return (
    <RequireAuth>
      <DashboardLayout title="Rewards" subtitle="Gamification state (points, streaks, badges) — MVP.">
        {error ? (
          <div className="mb-4 rounded border border-red-900/60 bg-red-950/40 p-3 text-sm text-red-200">{error}</div>
        ) : null}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 text-slate-100">
            <div className="text-sm text-slate-300">Points</div>
            <div className="mt-1 text-3xl font-bold">{data?.points ?? 0}</div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 text-slate-100">
            <div className="text-sm text-slate-300">Streak</div>
            <div className="mt-1 text-3xl font-bold">{data?.streak_days ?? 0} days</div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 text-slate-100">
            <div className="text-sm text-slate-300">Badges</div>
            <div className="mt-3 flex flex-wrap gap-2">
              {(data?.badges || []).length === 0 ? (
                <div className="text-sm text-slate-400">No badges yet.</div>
              ) : (
                (data?.badges || []).map((b: string) => (
                  <span key={b} className="rounded bg-slate-800 px-2 py-1 text-xs text-slate-100">
                    {b}
                  </span>
                ))
              )}
            </div>
          </div>
        </div>
      </DashboardLayout>
    </RequireAuth>
  );
}

