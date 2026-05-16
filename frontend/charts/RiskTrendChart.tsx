import {
  LineChart,
  Line,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

type Series = {
  dataKey: string;
  stroke: string;
  label: string;
};

export default function RiskTrendChart({
  title,
  data,
  series,
  yFormatter,
}: {
  title: string;
  data: Array<{ x: string; [key: string]: any }>;
  series: Series[];
  yFormatter?: (v: any) => string;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <div className="font-semibold text-slate-100">{title}</div>
      <div className="mt-3 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="x" tick={{ fontSize: 12 }} />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={(v) => (yFormatter ? yFormatter(v) : String(v))}
            />
            <Tooltip
              formatter={(v: any) => (yFormatter ? yFormatter(v) : String(v))}
              labelFormatter={(l) => l}
            />
            <Legend wrapperStyle={{ color: "#cbd5e1" }} />
            {series.map((item) => (
              <Line
                key={item.dataKey}
                type="monotone"
                dataKey={item.dataKey}
                stroke={item.stroke}
                dot={{ r: 3 }}
                name={item.label}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

