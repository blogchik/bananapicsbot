import { Calendar } from 'lucide-react';

interface DateRangePickerProps {
  value: number;
  onChange: (days: number) => void;
}

const presets = [
  { label: '7 days', value: 7 },
  { label: '14 days', value: 14 },
  { label: '30 days', value: 30 },
  { label: '90 days', value: 90 },
  { label: '365 days', value: 365 },
];

export function DateRangePicker({ value, onChange }: DateRangePickerProps) {
  return (
    <div className="relative inline-flex items-center gap-2">
      <Calendar className="w-4 h-4 text-muted-foreground" />
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="appearance-none bg-surface border border-surface-lighter/50 text-sm text-white rounded-lg px-3 py-2 pr-8 focus-ring cursor-pointer hover:border-banana-500/30 transition-colors duration-150"
      >
        {presets.map((preset) => (
          <option key={preset.value} value={preset.value}>
            Last {preset.label}
          </option>
        ))}
      </select>
      <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2">
        <svg
          className="w-4 h-4 text-muted-foreground"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>
  );
}
