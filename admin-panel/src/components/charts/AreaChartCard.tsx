import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { format, parseISO } from 'date-fns';

interface AreaChartCardProps {
  title: string;
  data: Array<Record<string, any>>;
  dataKey: string;
  xKey?: string;
  color?: string;
  loading?: boolean;
  formatValue?: (value: number) => string;
}

function CustomTooltip({
  active,
  payload,
  label,
  formatValue,
}: {
  active?: boolean;
  payload?: Array<{ value: number; dataKey: string }>;
  label?: string;
  formatValue?: (value: number) => string;
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
      <p className="text-xs text-muted-foreground mb-1">{formattedLabel}</p>
      {payload.map((entry, index) => (
        <p key={index} className="text-sm font-semibold text-white">
          {formatValue ? formatValue(entry.value) : entry.value.toLocaleString()}
        </p>
      ))}
    </div>
  );
}

export function AreaChartCard({
  title,
  data,
  dataKey,
  xKey = 'date',
  color = '#E6B800',
  loading,
  formatValue,
}: AreaChartCardProps) {
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
          <AreaChart data={data} margin={{ top: 4, right: 4, left: -12, bottom: 0 }}>
            <defs>
              <linearGradient id={`gradient-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.3} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
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
            <Tooltip content={<CustomTooltip formatValue={formatValue} />} />
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              fill={`url(#gradient-${dataKey})`}
              dot={false}
              activeDot={{
                r: 4,
                fill: color,
                stroke: '#1E1E1E',
                strokeWidth: 2,
              }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
