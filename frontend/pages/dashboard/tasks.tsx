import { useEffect, useState, useRef } from "react";
import RiskTrendChart from "../../charts/RiskTrendChart";
import DashboardLayout from "../../components/DashboardLayout";
import RequireAuth from "../../components/RequireAuth";
import TaskTracker from "../../components/TaskTracker";
import { useAuth } from "../../context/AuthContext";
import { addTask, getProgress, updateTask, deleteTask, rescheduleTaskToDate, getTaskRescheduleOptions, cancelAllRequests, listGoals, deleteGoal } from "../../services/api";
import { getGoalDisplayTitle, getGoalMeta, isAutoPredictionGoal, parseTaskMeta } from "../../services/goalAutomation";

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

export default function TasksPage() {
  const { userId } = useAuth();
  const [progress, setProgress] = useState<any | null>(null);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [busy, setBusy] = useState(true);
  const [goalDeleteBusyId, setGoalDeleteBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const storageKey = `tasksPageProgress-${userId || "anonymous"}`;
  const isMountedRef = useRef(true);

  const loadProgress = async () => {
    if (!isMountedRef.current) return;
    setBusy(true);
    setError(null);
    try {
      const p = await getProgress();
      if (isMountedRef.current) {
        setProgress(p);
        try {
          window.localStorage.setItem(storageKey, JSON.stringify(p));
        } catch {
          // ignore storage errors
        }
      }
    } catch (e: any) {
      if (isMountedRef.current) {
        setError(e?.response?.data?.detail || e?.message || "Failed to load progress.");
        setProgress(null);
      }
    } finally {
      if (isMountedRef.current) {
        setBusy(false);
      }
    }
  };

  const loadGoals = async () => {
    if (!isMountedRef.current) return;
    try {
      const res = await listGoals();
      if (isMountedRef.current) {
        setGoals((res?.data || []).filter((goal: Goal) => goal.status !== "cancelled"));
      }
    } catch (e) {
      if (isMountedRef.current) {
        console.error("Failed to load goals:", e);
      }
    }
  };

  useEffect(() => {
    if (!userId) return;
    isMountedRef.current = true;

    try {
      const saved = window.localStorage.getItem(storageKey);
      if (saved) {
        setProgress(JSON.parse(saved));
        setBusy(false);
      }
    } catch {
      // ignore storage errors
    }
    loadProgress();
    loadGoals();

    return () => {
      isMountedRef.current = false;
      cancelAllRequests();
    };
  }, [userId, storageKey]);

  const taskList = progress?.weekly_tasks?.tasks || [];
  const goalCards = goals.map((goal) => {
    const goalMeta = getGoalMeta(goal);
    const linkedTasks = taskList.filter((task: any) => parseTaskMeta(task.notes)?.goal_id === goal.id);
    const completedCount = linkedTasks.filter((task: any) => task.completed).length;
    const derivedProgress = linkedTasks.length ? Math.round((completedCount / linkedTasks.length) * 100) : Math.round(goal.progress_value || 0);
    return {
      goal,
      goalMeta,
      linkedTasks,
      completedCount,
      derivedProgress,
      title: getGoalDisplayTitle(goal),
      isAutomated: isAutoPredictionGoal(goal),
    };
  });

  return (
    <RequireAuth>
      <DashboardLayout
        title="Goals & Progress"
        subtitle="Track goal-driven preventive tasks, completion progress, and prediction-linked health trends in one place."
      >
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <TaskTracker
            userId={userId || "unknown-user"}
            tasks={taskList}
            weeklySummary={progress?.weekly_tasks || null}
            trackingWindow={progress?.task_calendar_range ?? progress?.date_range ?? null}
            onAddTask={async (p) => {
              await addTask(p);
              await loadProgress();
              await loadGoals();
            }}
            onToggleTask={async (p) => {
              await updateTask(p);
              await loadProgress();
              await loadGoals();
            }}
            onDeleteTask={async (taskId) => {
              await deleteTask(taskId);
              await loadProgress();
              await loadGoals();
            }}
            onGetRescheduleOptions={async (taskId) => {
              return await getTaskRescheduleOptions(taskId);
            }}
            onRescheduleTask={async (taskId, targetDate) => {
              await rescheduleTaskToDate(taskId, targetDate);
              await loadProgress();
              await loadGoals();
            }}
          />

          <div className="space-y-6">
            <div className="overflow-hidden rounded-2xl border border-slate-700/60 bg-gradient-to-b from-slate-900 to-slate-950 p-5 text-slate-100 shadow-xl shadow-slate-950/50">
              <div>
                <h2 className="text-lg font-semibold tracking-tight text-slate-50">Goal tracking layer</h2>
                <p className="mt-0.5 text-sm text-slate-400">Auto-generated goals from predictions and the tasks currently supporting them.</p>
              </div>

              {!goalCards.length ? (
                <div className="mt-6 rounded-xl border border-dashed border-slate-700 bg-slate-950/40 px-4 py-8 text-center text-sm text-slate-400">
                  Run a prediction to generate a prevention goal and linked tasks automatically.
                </div>
              ) : (
                <div className="mt-4 space-y-3">
                  {goalCards.map(({ goal, goalMeta, linkedTasks, completedCount, derivedProgress, title, isAutomated }) => (
                    <div key={goal.id} className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <div className="text-sm font-semibold text-slate-100">{title}</div>
                          <div className="mt-1 text-xs text-slate-400">
                            Created {new Date(goal.created_at).toLocaleString()}
                            {goal.deadline ? ` · Deadline ${goal.deadline}` : ""}
                          </div>
                          {goalMeta?.last_updated_at ? (
                            <div className="mt-1 text-xs text-slate-500">
                              Last updated {new Date(goalMeta.last_updated_at).toLocaleString()}
                            </div>
                          ) : null}
                        </div>
                        <div className="flex items-center gap-2">
                          {isAutomated ? (
                            <span className="rounded-full bg-indigo-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-indigo-200">
                              Auto Goal
                            </span>
                          ) : null}
                          <span className={`rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] ${
                            goalMeta?.status === "updated"
                              ? "bg-amber-500/10 text-amber-200"
                              : "bg-sky-500/10 text-sky-200"
                          }`}>
                            {goalMeta?.status === "updated" ? "Updated" : "Active"}
                          </span>
                          <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-200">
                            {derivedProgress}% progress
                          </span>
                          <button
                            type="button"
                            disabled={goalDeleteBusyId === goal.id}
                            onClick={async () => {
                              setGoalDeleteBusyId(goal.id);
                              setError(null);
                              try {
                                await deleteGoal(goal.id);
                                await loadGoals();
                                await loadProgress();
                              } catch (e: any) {
                                setError(e?.response?.data?.detail || e?.message || "Failed to delete goal.");
                              } finally {
                                setGoalDeleteBusyId(null);
                              }
                            }}
                            className="rounded-full border border-red-800 bg-red-950/40 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-red-200 transition hover:bg-red-950/60 disabled:opacity-50"
                          >
                            {goalDeleteBusyId === goal.id ? "Deleting..." : "Delete Goal"}
                          </button>
                        </div>
                      </div>

                      <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-800">
                        <div className="h-full rounded-full bg-emerald-400 transition-all" style={{ width: `${derivedProgress}%` }} />
                      </div>

                      <div className="mt-3 text-sm text-slate-300">
                        {linkedTasks.length
                          ? `${completedCount} of ${linkedTasks.length} linked task(s) completed in the current task window.`
                          : "No linked tasks are visible yet in the current calendar window."}
                      </div>

                      {linkedTasks.length ? (
                        <div className="mt-3 space-y-2">
                          {linkedTasks.map((task: any) => (
                            <div key={task.id} className="rounded-xl border border-slate-800 bg-slate-900/80 px-3 py-2 text-sm text-slate-200">
                              <div className="flex items-center justify-between gap-3">
                                <span>{task.title}</span>
                                <span className={`text-xs font-medium ${task.completed ? "text-emerald-300" : "text-slate-400"}`}>
                                  {task.completed ? "Completed" : task.task_date}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="overflow-hidden rounded-2xl border border-slate-700/60 bg-gradient-to-b from-slate-900 to-slate-950 p-5 text-slate-100 shadow-xl shadow-slate-950/50">
              <div>
                <h2 className="text-lg font-semibold tracking-tight text-slate-50">Health progress tracking</h2>
                <p className="mt-0.5 text-sm text-slate-400">Risk and health score trends from your saved predictions.</p>
              </div>
              {busy ? (
                <div className="mt-6 flex items-center gap-2 text-sm text-slate-400">
                  <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-600 border-t-indigo-400" aria-hidden />
                  Loading progress…
                </div>
              ) : null}
              {error ? (
                <div className="mt-4 rounded-xl border border-red-900/50 bg-red-950/40 p-4 text-sm text-red-200">{error}</div>
              ) : null}

              {!busy && !error && !progress?.predictions?.length ? (
                <div className="mt-6 rounded-xl border border-dashed border-slate-700 bg-slate-950/40 px-4 py-8 text-center text-sm text-slate-400">
                  No prediction history yet. Run a prediction from the Prediction page to see trends here.
                </div>
              ) : null}

              {!busy && !error && progress?.predictions?.length ? (
                <div className="mt-3 space-y-4">
                  <RiskTrendChart
                    title="Diabetes Risk Trend"
                    data={progress.predictions.map((p: any) => ({
                      x: new Date(p.created_at).toLocaleDateString(),
                      diabetes: Math.round(p.diabetes_risk * 100),
                    }))}
                    series={[{ dataKey: "diabetes", stroke: "#4f46e5", label: "Diabetes" }]}
                    yFormatter={(v) => `${v}%`}
                  />
                  <RiskTrendChart
                    title="Overall Health Score Trend"
                    data={progress.predictions.map((p: any) => ({
                      x: new Date(p.created_at).toLocaleDateString(),
                      score: p.overall_health_score,
                    }))}
                    series={[{ dataKey: "score", stroke: "#059669", label: "Health Score" }]}
                  />
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </DashboardLayout>
    </RequireAuth>
  );
}
