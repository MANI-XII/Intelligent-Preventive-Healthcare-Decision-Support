import { useEffect, useState, useRef } from "react";
import DashboardLayout from "../../components/DashboardLayout";
import RequireAuth from "../../components/RequireAuth";
import { ackAlert, getAlerts, cancelAllRequests } from "../../services/api";

type AlertItem = {
  id: number;
  created_at: string;
  severity: string;
  category: string;
  title: string;
  message: string;
  acknowledged: boolean;
};

function badgeClass(severity: string) {
  if (severity === "critical") return "bg-red-600 text-white";
  if (severity === "warning") return "bg-amber-500 text-black";
  return "bg-slate-700 text-slate-100";
}

export default function AlertsPage() {
  const [items, setItems] = useState<AlertItem[]>([]);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const isMountedRef = useRef(true);

  async function refresh() {
    if (!isMountedRef.current) return;
    try {
      const res = await getAlerts();
      if (isMountedRef.current) {
        setItems(res?.data || []);
      }
    } catch (e: any) {
      if (isMountedRef.current) {
        setError(e?.message || "Failed to load alerts");
      }
    }
  }

  useEffect(() => {
    isMountedRef.current = true;
    refresh();

    return () => {
      isMountedRef.current = false;
      cancelAllRequests();
    };
  }, []);

  return (
    <RequireAuth>
      <DashboardLayout title="Alerts" subtitle="Notifications triggered by abnormal readings or risk conditions (MVP).">
        {error ? (
          <div className="mb-4 rounded border border-red-900/60 bg-red-950/40 p-3 text-sm text-red-200">{error}</div>
        ) : null}

        <div className="rounded-lg border border-slate-800 bg-slate-900">
          <div className="flex items-center justify-between gap-3 border-b border-slate-800 p-4">
            <div className="text-sm font-semibold text-slate-100">Recent alerts</div>
            <button onClick={() => refresh()} className="rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm">
              Refresh
            </button>
          </div>
          <div className="divide-y divide-slate-800">
            {items.length === 0 ? (
              <div className="p-4 text-sm text-slate-300">No alerts yet.</div>
            ) : (
              items.map((a) => (
                <div key={a.id} className="p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`rounded px-2 py-1 text-xs font-semibold ${badgeClass(a.severity)}`}>
                          {a.severity}
                        </span>
                        <div className="truncate font-semibold text-slate-100">{a.title}</div>
                      </div>
                      <div className="mt-1 text-xs text-slate-400">
                        {a.category} · {a.created_at}
                      </div>
                      <div className="mt-2 text-sm text-slate-200">{a.message}</div>
                    </div>
                    <button
                      disabled={busyId === a.id}
                      onClick={async () => {
                        setBusyId(a.id);
                        try {
                          await ackAlert({ alert_id: a.id, acknowledged: !a.acknowledged });
                          await refresh();
                        } finally {
                          setBusyId(null);
                        }
                      }}
                      className="rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm disabled:opacity-50"
                    >
                      {a.acknowledged ? "Mark unack" : "Acknowledge"}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </DashboardLayout>
    </RequireAuth>
  );
}

