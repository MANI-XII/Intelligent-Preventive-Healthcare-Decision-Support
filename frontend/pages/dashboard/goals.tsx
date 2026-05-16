import { useEffect, useState, useRef } from "react";
import DashboardLayout from "../../components/DashboardLayout";
import RequireAuth from "../../components/RequireAuth";
import { createGoal, listGoals, updateGoal, deleteGoal, cancelAllRequests } from "../../services/api";

type Goal = {
  id: number;
  created_at: string;
  goal_type: string;
  target_value: number;
  deadline?: string | null;
  status: string;
  progress_value: number;
  notes?: string | null;
};

export default function GoalsPage() {
  const [items, setItems] = useState<Goal[]>([]);
  const [busy, setBusy] = useState(false);
  const [deleteBusyId, setDeleteBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const isMountedRef = useRef(true);

  const [goalType, setGoalType] = useState("steps");
  const [targetValue, setTargetValue] = useState<number>(8000);
  const [deadline, setDeadline] = useState<string>("");
  const [notes, setNotes] = useState<string>("");

  async function refresh() {
    if (!isMountedRef.current) return;
    try {
      const res = await listGoals();
      if (isMountedRef.current) {
        setItems(res?.data || []);
      }
    } catch (e: any) {
      if (isMountedRef.current) {
        console.error("Failed to refresh goals:", e);
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
      <DashboardLayout title="Goals" subtitle="Set health goals and track progress (MVP).">
        {error ? (
          <div className="mb-4 rounded border border-red-900/60 bg-red-950/40 p-3 text-sm text-red-200">{error}</div>
        ) : null}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 text-slate-100">
            <div className="font-semibold">Create a goal</div>
            <div className="mt-4 grid grid-cols-1 gap-3">
              <div>
                <label className="text-sm font-medium">Goal type</label>
                <select
                  className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2"
                  value={goalType}
                  onChange={(e) => setGoalType(e.target.value)}
                >
                  <option value="steps">Steps</option>
                  <option value="bmi">BMI</option>
                  <option value="glucose">Blood glucose</option>
                  <option value="sleep">Sleep minutes</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Target value</label>
                <input
                  type="number"
                  className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2"
                  value={targetValue}
                  onChange={(e) => setTargetValue(Number(e.target.value))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Deadline (optional)</label>
                <input
                  type="date"
                  className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2"
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value)}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Notes (optional)</label>
                <input
                  type="text"
                  className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-3">
              <button
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  setError(null);
                  try {
                    await createGoal({
                      goal_type: goalType,
                      target_value: targetValue,
                      deadline: deadline ? deadline : null,
                      notes: notes || null,
                    });
                    setNotes("");
                    await refresh();
                  } catch (e: any) {
                    setError(e?.response?.data?.detail || e?.message || "Failed to create goal");
                  } finally {
                    setBusy(false);
                  }
                }}
                className="rounded bg-indigo-500 px-4 py-2 text-white disabled:opacity-50"
              >
                {busy ? "Saving..." : "Create goal"}
              </button>
              <button onClick={() => refresh()} className="rounded border border-slate-700 bg-slate-950 px-4 py-2">
                Refresh
              </button>
            </div>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 text-slate-100">
            <div className="font-semibold">Your goals</div>
            <div className="mt-4 space-y-3">
              {items.length === 0 ? (
                <div className="text-sm text-slate-300">No goals yet.</div>
              ) : (
                items.map((g) => (
                  <div key={g.id} className="rounded border border-slate-800 bg-slate-950 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="font-semibold">
                        {g.goal_type} → {g.target_value}
                      </div>
                      <div className="text-xs text-slate-400">{g.status}</div>
                    </div>
                    <div className="mt-1 text-xs text-slate-400">
                      Created {g.created_at}
                      {g.deadline ? ` · Deadline ${g.deadline}` : ""}
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <label className="text-xs text-slate-400">Progress</label>
                      <input
                        type="number"
                        className="w-28 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
                        value={g.progress_value}
                        onChange={(e) => {
                          const v = Number(e.target.value);
                          setItems((prev) => prev.map((x) => (x.id === g.id ? { ...x, progress_value: v } : x)));
                        }}
                      />
                      <button
                        className="rounded border border-slate-700 bg-slate-950 px-3 py-1 text-sm"
                        onClick={async () => {
                          await updateGoal({ goal_id: g.id, progress_value: g.progress_value });
                          await refresh();
                        }}
                      >
                        Save
                      </button>
                      <button
                        className="rounded border border-slate-700 bg-slate-950 px-3 py-1 text-sm"
                        onClick={async () => {
                          await updateGoal({ goal_id: g.id, status: g.status === "active" ? "completed" : "active" });
                          await refresh();
                        }}
                      >
                        {g.status === "active" ? "Mark done" : "Reopen"}
                      </button>
                      <button
                        disabled={deleteBusyId === g.id}
                        className="rounded border border-red-800 bg-red-950/40 px-3 py-1 text-sm text-red-200 disabled:opacity-50"
                        onClick={async () => {
                          setDeleteBusyId(g.id);
                          setError(null);
                          try {
                            await deleteGoal(g.id);
                            await refresh();
                          } catch (e: any) {
                            setError(e?.response?.data?.detail || e?.message || "Failed to delete goal");
                          } finally {
                            setDeleteBusyId(null);
                          }
                        }}
                      >
                        {deleteBusyId === g.id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                    {g.notes ? <div className="mt-2 text-sm text-slate-300">{g.notes}</div> : null}
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
