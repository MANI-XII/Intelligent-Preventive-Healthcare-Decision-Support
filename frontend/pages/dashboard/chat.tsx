import { useEffect, useState } from "react";
import DashboardLayout from "../../components/DashboardLayout";
import RequireAuth from "../../components/RequireAuth";
import { chatWithAI } from "../../services/api";

type Msg = { role: "user" | "bot"; text: string };

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestedActions, setSuggestedActions] = useState<string[]>([
    "How do I lower diabetes risk?",
    "What is the preventive health index?",
    "How can I download my report?",
  ]);

  useEffect(() => {
    setMessages([
      {
        role: "bot",
        text: "Hi! Ask me about healthcare risks, recommendations, reports, goals, or the prediction workflow.",
      },
    ]);
  }, []);

  const sendMessage = async (message: string) => {
    const text = message.trim();
    if (!text || busy) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setBusy(true);
    setError(null);

    try {
      const res = await chatWithAI(text);
      setMessages((prev) => [...prev, { role: "bot", text: res?.reply || "OK" }]);
      if (res?.suggested_actions) {
        setSuggestedActions(res.suggested_actions.slice(0, 5));
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Chat failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <RequireAuth>
      <DashboardLayout title="Intelligent Chat" subtitle="Ask questions about healthcare, predictions, risk, and goals.">
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 text-slate-100">
          <div className="grid gap-4 lg:grid-cols-[1.5fr_0.8fr]">
            <div className="rounded border border-slate-800 bg-slate-950 p-4">
              <div className="h-[420px] overflow-auto rounded border border-slate-900 bg-slate-950 p-4">
                <div className="space-y-3">
                  {messages.map((m, idx) => (
                    <div
                      key={idx}
                      className={`max-w-[85%] rounded px-3 py-2 text-sm ${
                        m.role === "user" ? "ml-auto bg-indigo-500 text-white" : "bg-slate-800 text-slate-100"
                      }`}
                    >
                      {m.text}
                    </div>
                  ))}
                </div>
              </div>

              {error ? (
                <div className="mt-3 rounded border border-red-900/60 bg-red-950/40 p-3 text-sm text-red-200">{error}</div>
              ) : null}

              <div className="mt-4 flex items-center gap-2">
                <input
                  className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                  placeholder="Type a message..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={async (e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      await sendMessage(input);
                    }
                  }}
                  disabled={busy}
                />
                <button
                  className="rounded bg-indigo-500 px-4 py-2 text-sm text-white disabled:opacity-50"
                  disabled={busy}
                  onClick={async () => await sendMessage(input)}
                >
                  Send
                </button>
              </div>
            </div>

            <div className="rounded border border-slate-800 bg-slate-950 p-4">
              <div className="text-sm font-semibold text-slate-100">Suggested prompts</div>
              <div className="mt-3 space-y-2 text-sm text-slate-300">
                {suggestedActions.map((action, idx) => (
                  <button
                    key={idx}
                    className="w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-left text-slate-100 transition hover:border-indigo-500"
                    onClick={() => sendMessage(action)}
                    disabled={busy}
                  >
                    {action}
                  </button>
                ))}
              </div>
              <div className="mt-4 rounded border border-slate-800 bg-slate-900 p-3 text-sm text-slate-300">
                Tip: Ask the assistant about healthcare risk factors, how to improve your preventive index, or how to use the app features.
              </div>
            </div>
          </div>
        </div>
      </DashboardLayout>
    </RequireAuth>
  );
}

