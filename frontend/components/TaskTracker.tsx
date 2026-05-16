import { useMemo, useState } from "react";

type Task = {
  id: number;
  task_date: string;
  title: string;
  completed: boolean;
  completed_at: string | null;
  notes: string | null;
};

type TaskTrackerProps = {
  userId: string;
  tasks: Task[];
  weeklySummary: {
    total: number;
    completed: number;
    completion_rate: number;
    by_day: Array<{ date: string; completed: number; total: number; status?: string }>;
    health_condition?: {
      current_score: number;
      projected_score: number;
      condition: string;
      note: string;
    };
  } | null;
  trackingWindow?: { start: string; end: string } | null;
  onAddTask: (payload: { user_id: string; task_date: string; title: string; notes?: string }) => Promise<void>;
  onToggleTask: (payload: { user_id: string; task_id: number; completed: boolean; notes?: string | null }) => Promise<void>;
  onDeleteTask?: (taskId: number) => Promise<void>;
  onGetRescheduleOptions?: (taskId: number) => Promise<{
    task_id: number;
    title: string;
    current_date: string;
    options: Array<{ date: string; pending_count: number; label: string }>;
  }>;
  onRescheduleTask?: (taskId: number, targetDate: string) => Promise<void>;
};

function toISODate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function parseISODate(s: string): Date {
  const [y, m, d] = s.slice(0, 10).split("-").map(Number);
  return new Date(y, m - 1, d);
}

function monthMatrix(year: number, monthIndex: number): (number | null)[][] {
  const first = new Date(year, monthIndex, 1);
  const lastDay = new Date(year, monthIndex + 1, 0).getDate();
  const pad = first.getDay();
  const flat: (number | null)[] = [];
  for (let i = 0; i < pad; i++) flat.push(null);
  for (let d = 1; d <= lastDay; d++) flat.push(d);
  while (flat.length % 7 !== 0) flat.push(null);
  const rows: (number | null)[][] = [];
  for (let i = 0; i < flat.length; i += 7) rows.push(flat.slice(i, i + 7));
  return rows;
}

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;

export default function TaskTracker({
  userId,
  tasks,
  weeklySummary,
  trackingWindow,
  onAddTask,
  onToggleTask,
  onDeleteTask,
  onGetRescheduleOptions,
  onRescheduleTask,
}: TaskTrackerProps) {
  const [title, setTitle] = useState("");
  const [taskDate, setTaskDate] = useState(() => toISODate(new Date()));
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [deleteTaskId, setDeleteTaskId] = useState<number | null>(null);
  const [rescheduleTaskId, setRescheduleTaskId] = useState<number | null>(null);
  const [rescheduleOptions, setRescheduleOptions] = useState<Array<{ date: string; pending_count: number; label: string }>>([]);
  const [rescheduleTargetDate, setRescheduleTargetDate] = useState("");
  const [rescheduleTaskTitle, setRescheduleTaskTitle] = useState("");

  const view = useMemo(() => parseISODate(taskDate), [taskDate]);
  const [viewYear, setViewYear] = useState(view.getFullYear());
  const [viewMonth, setViewMonth] = useState(view.getMonth());
  const todayISO = toISODate(new Date());
  const weekRate = weeklySummary ? Math.round(weeklySummary.completion_rate * 100) : 0;

  const tasksByDate = useMemo(() => {
    const m = new Map<string, Task[]>();
    for (const t of tasks) {
      const key = t.task_date.slice(0, 10);
      if (!m.has(key)) m.set(key, []);
      m.get(key)!.push(t);
    }
    for (const arr of m.values()) {
      arr.sort((a, b) => a.id - b.id);
    }
    return m;
  }, [tasks]);

  const generatedPredictionTasks = useMemo(
    () => tasks.filter((task) => task.notes?.includes("Generated from prediction recommendations")),
    [tasks]
  );

  const byDayLookup = useMemo(() => {
    const m = new Map<string, { completed: number; total: number }>();
    if (!weeklySummary) return m;
    for (const row of weeklySummary.by_day) {
      m.set(row.date.slice(0, 10), { completed: row.completed, total: row.total });
    }
    return m;
  }, [weeklySummary]);

  const inTrackingWindow = useMemo(() => {
    if (!trackingWindow) return (_iso: string) => false;
    const a = trackingWindow.start.slice(0, 10);
    const b = trackingWindow.end.slice(0, 10);
    return (iso: string) => iso >= a && iso <= b;
  }, [trackingWindow]);

  const calendarRows = useMemo(() => monthMatrix(viewYear, viewMonth), [viewYear, viewMonth]);

  const selectedTasks = tasksByDate.get(taskDate.slice(0, 10)) ?? [];

  const goMonth = (delta: number) => {
    const d = new Date(viewYear, viewMonth + delta, 1);
    setViewYear(d.getFullYear());
    setViewMonth(d.getMonth());
  };

  const monthLabel = new Intl.DateTimeFormat(undefined, { month: "long", year: "numeric" }).format(
    new Date(viewYear, viewMonth, 1)
  );

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-700/60 bg-gradient-to-b from-slate-900 to-slate-950 shadow-xl shadow-slate-950/50">
      <div className="border-b border-slate-800/80 bg-slate-900/50 px-5 py-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold tracking-tight text-slate-50">Preventive task calendar</h2>
            <p className="mt-0.5 text-sm text-slate-400">
              Plan tasks by day and track your rolling weekly completion.
            </p>
            {generatedPredictionTasks.length ? (
              <div className="mt-3 inline-flex items-center gap-2 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 px-3 py-2 text-sm text-emerald-200">
                <span className="inline-flex h-2.5 w-2.5 rounded-full bg-emerald-400" />
                {generatedPredictionTasks.length === 1
                  ? "1 task was auto-generated from your latest prediction."
                  : `${generatedPredictionTasks.length} tasks were auto-generated from your latest prediction.`}
              </div>
            ) : null}
          </div>
          <div className="flex shrink-0 items-center gap-3 rounded-xl border border-slate-700/80 bg-slate-950/80 px-4 py-3">
            <div className="relative h-12 w-12">
              <svg className="h-12 w-12 -rotate-90" viewBox="0 0 36 36" aria-hidden>
                <circle cx="18" cy="18" r="15.5" fill="none" stroke="currentColor" strokeWidth="3" className="text-slate-800" />
                <circle
                  cx="18"
                  cy="18"
                  r="15.5"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeDasharray={`${(weekRate / 100) * 97.4} 97.4`}
                  className="text-emerald-400 transition-[stroke-dasharray] duration-500"
                />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-slate-100">
                {weeklySummary ? `${weekRate}%` : "—"}
              </span>
            </div>
            <div className="text-left">
              <div className="text-xs font-medium uppercase tracking-wide text-slate-500">This week</div>
              <div className="text-sm font-medium text-slate-200">
                {weeklySummary ? (
                  <>
                    {weeklySummary.completed} of {weeklySummary.total} done
                  </>
                ) : (
                  "No data yet"
                )}
              </div>
            </div>
          </div>
        </div>

        {weeklySummary && weeklySummary.by_day.length > 0 ? (
          <>
            <div className="mt-4 flex gap-2 overflow-x-auto pb-1 pt-1">
              {[...weeklySummary.by_day]
                .sort((a, b) => a.date.localeCompare(b.date))
                .map((day) => {
                  const iso = day.date.slice(0, 10);
                  const pct = day.total ? Math.round((day.completed / day.total) * 100) : 0;
                  const short = new Intl.DateTimeFormat(undefined, { weekday: "short", day: "numeric" }).format(parseISODate(iso));
                  const active = iso === taskDate.slice(0, 10);
                  const status = (day as { status?: string }).status || (day.completed > 0 ? "improved" : "stable");
                  const dotClass = status === "improved" ? "bg-emerald-400" : "bg-slate-600";
                  return (
                    <button
                      key={iso}
                      type="button"
                      onClick={() => {
                        setTaskDate(iso);
                        const pd = parseISODate(iso);
                        setViewYear(pd.getFullYear());
                        setViewMonth(pd.getMonth());
                      }}
                      className={`flex min-w-[4.5rem] flex-col items-stretch rounded-lg border px-2 py-2 text-left transition ${
                        active
                          ? "border-indigo-500/80 bg-indigo-500/15 ring-1 ring-indigo-500/40"
                          : "border-slate-700/80 bg-slate-950/60 hover:border-slate-600"
                      }`}
                    >
                      <span className="text-[10px] font-medium uppercase tracking-wide text-slate-500">{short}</span>
                      <span className="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-800">
                        <span
                          className={`block h-full rounded-full transition-all ${pct === 100 ? "bg-emerald-400" : pct > 0 ? "bg-indigo-400" : "bg-slate-700"}`}
                          style={{ width: `${pct}%` }}
                        />
                      </span>
                      <span className="mt-1 flex items-center justify-between text-[11px] text-slate-400">
                        <span>{day.total ? `${day.completed}/${day.total}` : "—"}</span>
                        <span className={`inline-flex h-2.5 w-2.5 rounded-full ${dotClass}`} />
                      </span>
                    </button>
                  );
                })}
            </div>
            {weeklySummary.health_condition ? (
              <div className="mt-4 rounded-2xl border border-slate-800/80 bg-slate-950/80 p-4 text-slate-200">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-slate-100">Health condition update</div>
                    <div className="mt-1 text-xs text-slate-500">Based on your completed tasks this week.</div>
                  </div>
                  <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-300">
                    {weeklySummary.health_condition.condition}
                  </span>
                </div>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border border-slate-700/80 bg-slate-900/80 p-3">
                    <div className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Current health score</div>
                    <div className="mt-2 text-2xl font-semibold text-slate-100">{weeklySummary.health_condition.current_score}</div>
                  </div>
                  <div className="rounded-2xl border border-slate-700/80 bg-slate-900/80 p-3">
                    <div className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Projected score</div>
                    <div className="mt-2 text-2xl font-semibold text-emerald-300">{weeklySummary.health_condition.projected_score}</div>
                  </div>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-400">{weeklySummary.health_condition.note}</p>
              </div>
            ) : null}
          </>
        ) : null}
      </div>

      <div className="p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => goMonth(-1)}
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-700 bg-slate-900 text-slate-200 transition hover:bg-slate-800"
              aria-label="Previous month"
            >
              <ChevronLeftIcon />
            </button>
            <button
              type="button"
              onClick={() => goMonth(1)}
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-700 bg-slate-900 text-slate-200 transition hover:bg-slate-800"
              aria-label="Next month"
            >
              <ChevronRightIcon />
            </button>
            <h3 className="ml-1 min-w-[10rem] text-base font-semibold text-slate-100">{monthLabel}</h3>
          </div>
          <button
            type="button"
            onClick={() => {
              const t = toISODate(new Date());
              setTaskDate(t);
              const pd = parseISODate(t);
              setViewYear(pd.getFullYear());
              setViewMonth(pd.getMonth());
            }}
            className="rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-1.5 text-sm font-medium text-slate-100 transition hover:bg-slate-700"
          >
            Today
          </button>
        </div>

        <div className="grid grid-cols-7 gap-1 text-center text-[11px] font-medium uppercase tracking-wide text-slate-500">
          {WEEKDAYS.map((d) => (
            <div key={d} className="py-2">
              {d}
            </div>
          ))}
        </div>

        <div className="grid grid-flow-row gap-1">
          {calendarRows.map((week, wi) => (
            <div key={wi} className="grid grid-cols-7 gap-1">
              {week.map((day, di) => {
                if (day === null) {
                  return <div key={`e-${wi}-${di}`} className="aspect-square min-h-[2.75rem]" />;
                }
                const iso = `${viewYear}-${String(viewMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
                const isSelected = iso === taskDate.slice(0, 10);
                const isTodayCell = iso === todayISO;
                const dayTasks = tasksByDate.get(iso) ?? [];
                const stats = byDayLookup.get(iso);
                const inWin = inTrackingWindow(iso);
                const doneAll = stats && stats.total > 0 && stats.completed === stats.total;
                const partial = stats && stats.total > 0 && stats.completed > 0 && stats.completed < stats.total;

                return (
                  <button
                    key={iso}
                    type="button"
                    onClick={() => setTaskDate(iso)}
                    className={`group relative flex aspect-square min-h-[2.75rem] flex-col items-center justify-center rounded-xl border text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 ${
                      isSelected
                        ? "border-indigo-500 bg-indigo-500/20 text-white shadow-md shadow-indigo-900/30"
                        : "border-transparent bg-slate-900/40 text-slate-200 hover:border-slate-600 hover:bg-slate-800/80"
                    } ${isTodayCell && !isSelected ? "ring-1 ring-emerald-500/50" : ""} ${
                      inWin && !isSelected ? "bg-indigo-950/20" : ""
                    }`}
                  >
                    <span>{day}</span>
                    {dayTasks.length > 0 ? (
                      <span className="mt-0.5 flex h-5 items-center justify-center rounded-full bg-slate-800 px-1.5 text-[10px] font-semibold text-slate-300 group-hover:bg-slate-700">
                        {dayTasks.length}
                      </span>
                    ) : stats && stats.total > 0 ? (
                      <span
                        className={`mt-0.5 h-1.5 w-1.5 rounded-full ${doneAll ? "bg-emerald-400" : partial ? "bg-amber-400" : "bg-slate-600"}`}
                        title={`${stats.completed}/${stats.total} completed`}
                      />
                    ) : null}
                  </button>
                );
              })}
            </div>
          ))}
        </div>

        {trackingWindow ? (
          <p className="mt-3 text-xs text-slate-500">
            Highlighted week strip matches your dashboard tracking window ({trackingWindow.start.slice(0, 10)} →{" "}
            {trackingWindow.end.slice(0, 10)}). Task counts on the grid reflect tasks in that period.
          </p>
        ) : null}
      </div>

      <div className="border-t border-slate-800/80 bg-slate-900/30 px-5 py-5">
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-slate-200">Add a task</h3>
          <p className="mt-0.5 text-xs text-slate-500">
            Selected day:{" "}
            <time dateTime={taskDate} className="font-medium text-slate-300">
              {new Intl.DateTimeFormat(undefined, { weekday: "long", month: "long", day: "numeric" }).format(parseISODate(taskDate))}
            </time>
          </p>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="md:col-span-2">
            <label htmlFor="task-title" className="text-xs font-medium text-slate-400">
              Title
            </label>
            <input
              id="task-title"
              className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-100 shadow-inner placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. 30-minute walk, blood pressure check"
            />
          </div>
          <div>
            <label htmlFor="task-date" className="text-xs font-medium text-slate-400">
              Date
            </label>
            <input
              id="task-date"
              type="date"
              className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              value={taskDate}
              onChange={(e) => {
                const v = e.target.value;
                setTaskDate(v);
                if (v) {
                  const pd = parseISODate(v);
                  setViewYear(pd.getFullYear());
                  setViewMonth(pd.getMonth());
                }
              }}
            />
          </div>
          <div>
            <label htmlFor="task-notes" className="text-xs font-medium text-slate-400">
              Notes <span className="font-normal text-slate-500">(optional)</span>
            </label>
            <input
              id="task-notes"
              className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Reminder or context"
            />
          </div>
        </div>

        <div className="mt-4">
          <button
            disabled={busy || !title.trim()}
            onClick={async () => {
              setBusy(true);
              try {
                await onAddTask({
                  user_id: userId,
                  task_date: taskDate,
                  title: title.trim(),
                  notes: notes.trim() ? notes.trim() : undefined,
                });
                setTitle("");
                setNotes("");
              } finally {
                setBusy(false);
              }
            }}
            className="inline-flex w-full items-center justify-center rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-900/30 transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-45 sm:w-auto"
          >
            {busy ? "Adding…" : "Add task"}
          </button>
        </div>
      </div>

      <div className="border-t border-slate-800/80 px-5 py-5">
        <div className="mb-3 flex items-baseline justify-between gap-2">
          <h3 className="text-sm font-semibold text-slate-200">
            Tasks on{" "}
            {new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(parseISODate(taskDate))}
          </h3>
          {selectedTasks.length > 0 ? (
            <span className="text-xs text-slate-500">
              {selectedTasks.filter((t) => t.completed).length}/{selectedTasks.length} done
            </span>
          ) : null}
        </div>

        {selectedTasks.length ? (
          <ul className="space-y-2">
            {selectedTasks.map((t) => {
              const taskDateISO = t.task_date.slice(0, 10);
              const isTaskInPast = taskDateISO < todayISO;
              const isMissedTask = isTaskInPast && !t.completed;
              const canToggle = taskDateISO === todayISO;

              return (
                <li
                  key={t.id}
                  className={`flex items-start gap-3 rounded-xl border px-3 py-3 transition ${
                    t.completed ? "border-slate-800/80 bg-slate-950/50" : "border-slate-700/80 bg-slate-900/40"
                  }`}
                >
                  <button
                    type="button"
                    role="checkbox"
                    aria-checked={t.completed}
                    disabled={!canToggle}
                    onClick={() =>
                      canToggle &&
                      onToggleTask({ user_id: userId, task_id: t.id, completed: !t.completed, notes: t.notes })
                    }
                    className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border-2 transition ${
                      canToggle
                        ? t.completed
                          ? "border-emerald-500 bg-emerald-500 text-white cursor-pointer"
                          : "border-slate-500 hover:border-indigo-400 cursor-pointer"
                        : "border-slate-600 bg-slate-800 text-slate-500 cursor-not-allowed"
                    }`}
                    title={!canToggle ? (isTaskInPast ? "Missed tasks must be rescheduled before completion" : "You can mark this task complete only on its scheduled date") : ""}
                  >
                    {t.completed ? (
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    ) : null}
                  </button>
                  <div className="min-w-0 flex-1">
                    <div className={`font-medium leading-snug ${t.completed ? "text-slate-500 line-through" : "text-slate-100"}`}>
                      {t.title}
                    </div>
                    {t.notes ? <p className="mt-1 text-xs text-slate-500">{t.notes}</p> : null}
                    {!t.completed && taskDateISO > todayISO ? (
                      <p className="mt-1 text-xs text-sky-300">Upcoming task. Completion unlocks on {new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(parseISODate(taskDateISO))}.</p>
                    ) : null}
                    {isMissedTask ? (
                      <p className="mt-1 text-xs text-amber-300">Missed task. Reschedule it to a future date before marking it complete.</p>
                    ) : null}
                  </div>
                  <div className="flex shrink-0 gap-1">
                    {isMissedTask && onRescheduleTask ? (
                      <button
                        type="button"
                        onClick={async () => {
                          if (!onGetRescheduleOptions) return;
                          setBusy(true);
                          try {
                            const response = await onGetRescheduleOptions(t.id);
                            setRescheduleTaskId(t.id);
                            setRescheduleTaskTitle(response.title);
                            setRescheduleOptions(response.options);
                            setRescheduleTargetDate(response.options[0]?.date ?? "");
                          } finally {
                            setBusy(false);
                          }
                        }}
                        className="inline-flex items-center justify-center rounded-lg border border-amber-700/50 bg-amber-950/40 px-2 py-1.5 text-xs font-medium text-amber-200 transition hover:bg-amber-950/60"
                        title="Reschedule this missed task"
                      >
                        Reschedule
                      </button>
                    ) : null}
                    {onDeleteTask ? (
                      <button
                        type="button"
                        onClick={() => setDeleteTaskId(t.id)}
                        className="inline-flex items-center justify-center rounded-lg border border-red-700/50 bg-red-950/40 px-2 py-1.5 text-xs font-medium text-red-200 transition hover:bg-red-950/60"
                        title="Delete this task"
                      >
                        Delete
                      </button>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ul>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-700 bg-slate-950/40 px-4 py-8 text-center">
            <p className="text-sm text-slate-400">No tasks for this day.</p>
            <p className="mt-1 text-xs text-slate-600">Add one above or pick another date on the calendar.</p>
          </div>
        )}
      </div>

      {deleteTaskId && (
        <div className="border-t border-slate-800/80 bg-red-950/20 px-5 py-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-red-200">Confirm deletion</p>
              <p className="mt-0.5 text-xs text-red-300">This task will be permanently removed. This action cannot be undone.</p>
            </div>
            <div className="flex shrink-0 gap-2">
              <button
                type="button"
                onClick={() => setDeleteTaskId(null)}
                className="rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-1.5 text-sm font-medium text-slate-100 transition hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={async () => {
                  if (onDeleteTask) {
                    setBusy(true);
                    try {
                      await onDeleteTask(deleteTaskId);
                      setDeleteTaskId(null);
                    } finally {
                      setBusy(false);
                    }
                  }
                }}
                disabled={busy}
                className="rounded-lg bg-red-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-red-500 disabled:opacity-50"
              >
                {busy ? "Deleting…" : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      {rescheduleTaskId && (
        <div className="border-t border-slate-800/80 bg-amber-950/20 px-5 py-4">
          <div className="flex flex-col gap-4">
            <div>
              <p className="text-sm font-semibold text-amber-200">Reschedule missed task</p>
              <p className="mt-0.5 text-xs text-amber-300">Choose a new date for &quot;{rescheduleTaskTitle}&quot;. Your other unfinished future tasks will stay where they are.</p>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {rescheduleOptions.map((option) => (
                <label
                  key={option.date}
                  className={`rounded-lg border px-3 py-2 text-sm transition ${
                    rescheduleTargetDate === option.date
                      ? "border-amber-400 bg-amber-500/10 text-amber-100"
                      : "border-slate-700 bg-slate-900/40 text-slate-200"
                  }`}
                >
                  <input
                    type="radio"
                    name="reschedule-date"
                    value={option.date}
                    checked={rescheduleTargetDate === option.date}
                    onChange={() => setRescheduleTargetDate(option.date)}
                    className="sr-only"
                  />
                  <div className="font-medium">
                    {new Intl.DateTimeFormat(undefined, { weekday: "short", month: "short", day: "numeric" }).format(parseISODate(option.date))}
                  </div>
                  <div className="mt-1 text-xs text-slate-400">{option.label}</div>
                </label>
              ))}
            </div>
            <div className="flex shrink-0 gap-2">
              <button
                type="button"
                onClick={() => {
                  setRescheduleTaskId(null);
                  setRescheduleOptions([]);
                  setRescheduleTargetDate("");
                  setRescheduleTaskTitle("");
                }}
                className="rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-1.5 text-sm font-medium text-slate-100 transition hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={async () => {
                  if (onRescheduleTask && rescheduleTargetDate) {
                    setBusy(true);
                    try {
                      await onRescheduleTask(rescheduleTaskId, rescheduleTargetDate);
                      setRescheduleTaskId(null);
                      setRescheduleOptions([]);
                      setRescheduleTargetDate("");
                      setRescheduleTaskTitle("");
                    } finally {
                      setBusy(false);
                    }
                  }
                }}
                disabled={busy || !rescheduleTargetDate}
                className="rounded-lg bg-amber-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-amber-500 disabled:opacity-50"
              >
                {busy ? "Rescheduling…" : "Reschedule"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ChevronLeftIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
    </svg>
  );
}

function ChevronRightIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
    </svg>
  );
}
