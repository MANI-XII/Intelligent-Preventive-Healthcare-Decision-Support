import { ElementType } from "react";

type Props = {
  title: string;
  value: string | number;
  level?: string;
  icon?: ElementType;
};

const levelColor = (level?: string) => {
  const l = (level || "").toLowerCase();
  if (l === "high") return "bg-red-950/60 text-red-200 border-red-900";
  if (l === "moderate") return "bg-amber-950/60 text-amber-200 border-amber-900";
  if (l === "low") return "bg-emerald-950/60 text-emerald-200 border-emerald-900";
  return "bg-slate-900 text-slate-200 border-slate-800";
};

export default function RiskCard({ title, value, level, icon: Icon }: Props) {
  return (
    <div className={`rounded-lg border p-4 ${levelColor(level)}`}>
      <div className="flex items-center gap-3">
        {Icon ? <Icon className="h-5 w-5 text-slate-300" /> : null}
        <div className="text-sm font-medium">{title}</div>
      </div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      {level ? <div className="mt-1 text-xs font-medium">{level} Risk</div> : null}
    </div>
  );
}

