type Explanation = {
  shap_chart_base64?: string;
  contributions?: Record<string, number>;
  feature_importance?: Record<string, number>;
};

export default function ExplainableChart({ explanations }: { explanations?: Explanation }) {
  const chart = explanations?.shap_chart_base64;
  const contributions = explanations?.contributions ?? {};
  const keys = Object.keys(contributions);

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <div className="font-semibold text-slate-100">Explainable AI (SHAP)</div>
      {chart ? (
        <div className="mt-3">
          <img
            alt="SHAP explanation chart"
            className="max-w-full rounded border border-slate-800 bg-slate-950"
            src={`data:image/png;base64,${chart}`}
          />
        </div>
      ) : (
        <div className="mt-3 text-sm text-slate-300">
          Run prediction to see SHAP explanations.
        </div>
      )}
      {keys.length ? (
        <div className="mt-4 text-sm">
          <div className="font-medium text-slate-200">Top contributions</div>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {keys
              .sort((a, b) => Math.abs((contributions[b] ?? 0) as number) - Math.abs((contributions[a] ?? 0) as number))
              .map((k) => (
                <div key={k} className="rounded border border-slate-800 bg-slate-950 px-2 py-2">
                  <div className="text-xs text-slate-400">{k}</div>
                  <div className="font-semibold">{(contributions[k] ?? 0).toFixed(3)}</div>
                </div>
              ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

