import { useEffect, useState, useRef } from "react";
import DashboardLayout from "../../components/DashboardLayout";
import RequireAuth from "../../components/RequireAuth";
import { addBehavior, listBehavior, cancelAllRequests } from "../../services/api";

type LogItem = {
  id: number;
  created_at: string;
  category: string;
  value: any;
};

export default function BehaviorPage() {
  const [items, setItems] = useState<LogItem[]>([]);
  const [category, setCategory] = useState("activity");
  const [valueText, setValueText] = useState("{\"note\":\"Walked 20 minutes\"}");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isMountedRef = useRef(true);

  async function refresh() {
    if (!isMountedRef.current) return;
    try {
      const res = await listBehavior();
      if (isMountedRef.current) {
        setItems(res?.data || []);
      }
    } catch (e: any) {
      if (isMountedRef.current) {
        console.error("Failed to refresh behavior logs:", e);
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
      <DashboardLayout title="Behavior" subtitle="Log diet/sleep/activity habits for long-term tracking (MVP).">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 text-slate-100">
            <div className="font-semibold">Add behavior log</div>
            <div className="mt-4 grid grid-cols-1 gap-3">
              <div>
                <label className="text-sm font-medium">Category</label>
                <select
                  className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                >
                  <option value="diet">Diet</option>
                  <option value="sleep">Sleep</option>
                  <option value="activity">Activity</option>
                  <option value="medication">Medication</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Value (JSON)</label>
                <textarea
                  className="mt-1 h-28 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-xs"
                  value={valueText}
                  onChange={(e) => setValueText(e.target.value)}
                />
              </div>
            </div>

            {error ? (
              <div className="mt-4 rounded border border-red-900/60 bg-red-950/40 p-3 text-sm text-red-200">
                {error}
              </div>
            ) : null}

            <div className="mt-4 flex items-center gap-3">
              <button
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  setError(null);
                  try {
                    const parsed = JSON.parse(valueText || "{}");
                    await addBehavior({ category, value: parsed });
                    await refresh();
                  } catch (e: any) {
                    setError(e?.message || "Failed to add log (ensure JSON is valid)");
                  } finally {
                    setBusy(false);
                  }
                }}
                className="rounded bg-indigo-500 px-4 py-2 text-white disabled:opacity-50"
              >
                {busy ? "Saving..." : "Save log"}
              </button>
              <button onClick={() => refresh()} className="rounded border border-slate-700 bg-slate-950 px-4 py-2">
                Refresh
              </button>
            </div>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 text-slate-100">
            <div className="font-semibold">Recent logs</div>
            <div className="mt-4 space-y-3">
              {items.length === 0 ? (
                <div className="text-sm text-slate-300">No logs yet.</div>
              ) : (
                items.map((x) => (
                  <div key={x.id} className="rounded border border-slate-800 bg-slate-950 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-semibold">{x.category}</div>
                      <div className="text-xs text-slate-400">{x.created_at}</div>
                    </div>
                    <pre className="mt-2 whitespace-pre-wrap rounded border border-slate-800 bg-slate-950 p-2 text-xs text-slate-200">
                      {JSON.stringify(x.value, null, 2)}
                    </pre>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </DashboardLayout>
    </RequireAuth>
  );
}

