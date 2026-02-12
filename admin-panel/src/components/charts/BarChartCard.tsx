import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface BarChartCardProps {
  title: string;
  data: Array<Record<string, any>>;
  dataKey: string;
  nameKey: string;
  color?: string;
  loading?: boolean;
  layout?: 'horizontal' | 'vertical';
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ value: number; payload: Record<string, any> }>;
}) {
  if (!active || !payload?.length) return null;

  const entry = payload[0];
  return (
    <div className="bg-dark-400 border border-surface-lighter/50 rounded-lg px-3 py-2 shadow-elevated">
      <p className="text-xs text-muted-foreground mb-1">
        {entry.payload.model_name || entry.payload.name}
      </p>
      <p className="text-sm font-semibold text-white">
        {entry.value.toLocaleString()} generations
      </p>
      {entry.payload.credits != null && (
        <p className="text-xs text-muted-foreground">
          {entry.payload.credits.toLocaleString()} credits
        </p>
      )}
    </div>
  );
}

// A set of distinguishable colors for bars
const BAR_COLORS = [
  '#E6B800',
  '#FFCC33',
  '#FFD966',
  '#B38F00',
  '#FFE699',
  '#806600',
  '#FFF0C2',
  '#4D3D00',
];

export function BarChartCard({
  title,
  data,
  dataKey,
  nameKey,
  loading,
  layout = 'vertical',
}: BarChartCardProps) {
  if (loading) {
    return (
      <div className="card-admin p-6">
        <div className="h-4 w-40 bg-surface-light rounded animate-pulse-soft mb-6" />
        <div className="h-64 bg-surface-light/30 rounded-lg animate-pulse-soft" />
      </div>
    );
  }

  const isHorizontal = layout === 'horizontal';

  return (
    <div className="card-admin p-6">
      <h3 className="text-sm font-semibold text-white mb-4">{title}</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout={isHorizontal ? 'vertical' : 'horizontal'}
            margin={
              isHorizontal
                ? { top: 4, right: 16, left: 0, bottom: 0 }
                : { top: 4, right: 4, left: -12, bottom: 0 }
            }
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255,255,255,0.05)"
              horizontal={isHorizontal}
              vertical={!isHorizontal}
            />
            {isHorizontal ? (
              <>
                <XAxis
                  type="number"
                  tick={{ fill: '#737373', fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => {
                    if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
                    return value;
                  }}
                />
                <YAxis
                  type="category"
                  dataKey={nameKey}
                  tick={{ fill: '#A3A3A3', fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                  width={100}
                />
              </>
            ) : (
              <>
                <XAxis
                  dataKey={nameKey}
                  tick={{ fill: '#A3A3A3', fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
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
              </>
            )}
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
            <Bar
              dataKey={dataKey}
              radius={isHorizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]}
              maxBarSize={32}
            >
              {data.map((_entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={BAR_COLORS[index % BAR_COLORS.length]}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
