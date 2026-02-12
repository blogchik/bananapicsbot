import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { format, parseISO } from 'date-fns';

interface LineDef {
  dataKey: string;
  label: string;
  color: string;
}

interface MultiLineChartCardProps {
  title: string;
  data: Array<Record<string, any>>;
  lines: LineDef[];
  xKey?: string;
  loading?: boolean;
}

function CustomTooltip({
  active,
  payload,
  label,
  lines,
}: {
  active?: boolean;
  payload?: Array<{ value: number; dataKey: string }>;
  label?: string;
  lines: LineDef[];
}) {
  if (!active || !payload?.length) return null;

  let formattedLabel = label || '';
  try {
    if (label) {
      formattedLabel = format(parseISO(label), 'MMM d, yyyy');
    }
  } catch {
    // use raw label if parsing fails
  }

  return (
    <div className="bg-dark-400 border border-surface-lighter/50 rounded-lg px-3 py-2 shadow-elevated">
      <p className="text-xs text-muted-foreground mb-1.5">{formattedLabel}</p>
      {payload.map((entry, index) => {
        const lineDef = lines.find((l) => l.dataKey === entry.dataKey);
        return (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: lineDef?.color || '#fff' }}
            />
            <span className="text-muted-foreground text-xs">
              {lineDef?.label || entry.dataKey}:
            </span>
            <span className="font-semibold text-white text-xs">
              {entry.value.toLocaleString()}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function CustomLegend({
  lines,
}: {
  lines: LineDef[];
}) {
  return (
    <div className="flex items-center justify-center gap-4 mt-2">
      {lines.map((line) => (
        <div key={line.dataKey} className="flex items-center gap-1.5">
          <div
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: line.color }}
          />
          <span className="text-xs text-muted-foreground">{line.label}</span>
        </div>
      ))}
    </div>
  );
}

export function MultiLineChartCard({
  title,
  data,
  lines,
  xKey = 'date',
  loading,
}: MultiLineChartCardProps) {
  if (loading) {
    return (
      <div className="card-admin p-6">
        <div className="h-4 w-40 bg-surface-light rounded animate-pulse-soft mb-6" />
        <div className="h-64 bg-surface-light/30 rounded-lg animate-pulse-soft" />
      </div>
    );
  }

  return (
    <div className="card-admin p-6">
      <h3 className="text-sm font-semibold text-white mb-4">{title}</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 4, right: 4, left: -12, bottom: 0 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255,255,255,0.05)"
              vertical={false}
            />
            <XAxis
              dataKey={xKey}
              tick={{ fill: '#737373', fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => {
                try {
                  return format(parseISO(value), 'MMM d');
                } catch {
                  return value;
                }
              }}
            />
            <YAxis
              tick={{ fill: '#737373', fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => {
                if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
                return value;
              }}
            />
            <Tooltip content={<CustomTooltip lines={lines} />} />
            <Legend content={() => <CustomLegend lines={lines} />} />
            {lines.map((line) => (
              <Line
                key={line.dataKey}
                type="monotone"
                dataKey={line.dataKey}
                stroke={line.color}
                strokeWidth={2}
                dot={false}
                activeDot={{
                  r: 4,
                  fill: line.color,
                  stroke: '#1E1E1E',
                  strokeWidth: 2,
                }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
