import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Settings,
  Gift,
  DollarSign,
  Users,
  Gauge,
  Save,
  Loader2,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Zap,
  Shield,
  Clock,
  Server,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { settingsApi, type SystemSetting } from '@/api/settings';

// --- Setting Definitions ---

interface SettingFieldDef {
  key: string;
  label: string;
  description: string;
  type: 'number' | 'text' | 'boolean';
  min?: number;
  max?: number;
  step?: string;
}

interface SettingSectionDef {
  title: string;
  icon: LucideIcon;
  fields: SettingFieldDef[];
}

const SETTING_SECTIONS: SettingSectionDef[] = [
  {
    title: 'Trial Settings',
    icon: Gift,
    fields: [
      {
        key: 'trial_generations_limit',
        label: 'Trial Generations Limit',
        description: 'Number of free generations for new users',
        type: 'number',
        min: 0,
        max: 100,
      },
    ],
  },
  {
    title: 'Pricing & Credits',
    icon: DollarSign,
    fields: [
      {
        key: 'generation_price_markup',
        label: 'Generation Price Markup',
        description: 'Credits added to base Wavespeed price for each generation',
        type: 'number',
        min: 0,
      },
      {
        key: 'stars_exchange_numerator',
        label: 'Stars Exchange Numerator',
        description: 'Credits received (numerator / denominator × stars paid)',
        type: 'number',
        min: 1,
      },
      {
        key: 'stars_exchange_denominator',
        label: 'Stars Exchange Denominator',
        description: 'Stars paid (numerator / denominator × stars paid)',
        type: 'number',
        min: 1,
      },
      {
        key: 'stars_min_amount',
        label: 'Minimum Stars Purchase',
        description: 'Minimum number of stars for a purchase',
        type: 'number',
        min: 1,
      },
    ],
  },
  {
    title: 'Referral Program',
    icon: Users,
    fields: [
      {
        key: 'referral_bonus_percent',
        label: 'Referral Bonus Percent',
        description: 'Percentage of referred user purchases credited as bonus',
        type: 'number',
        min: 0,
        max: 100,
      },
      {
        key: 'referral_join_bonus',
        label: 'Referral Join Bonus',
        description: 'Credits awarded to referrer when a new user joins',
        type: 'number',
        min: 0,
      },
    ],
  },
  {
    title: 'Generation Limits',
    icon: Zap,
    fields: [
      {
        key: 'max_parallel_generations_per_user',
        label: 'Max Parallel Generations',
        description: 'Maximum concurrent generations per user',
        type: 'number',
        min: 1,
        max: 10,
      },
      {
        key: 'generation_poll_interval_seconds',
        label: 'Poll Interval (seconds)',
        description: 'How often to check generation status',
        type: 'number',
        min: 1,
        max: 30,
      },
      {
        key: 'generation_poll_max_duration_seconds',
        label: 'Max Poll Duration (seconds)',
        description: 'Maximum time to wait for generation completion',
        type: 'number',
        min: 60,
        max: 600,
      },
    ],
  },
  {
    title: 'Rate Limits',
    icon: Shield,
    fields: [
      {
        key: 'rate_limit_rps',
        label: 'Requests Per Second',
        description: 'API rate limit (requests per second)',
        type: 'number',
        min: 1,
        max: 100,
      },
      {
        key: 'rate_limit_burst',
        label: 'Burst Limit',
        description: 'Maximum burst requests allowed',
        type: 'number',
        min: 1,
        max: 200,
      },
    ],
  },
  {
    title: 'Wavespeed API',
    icon: Server,
    fields: [
      {
        key: 'wavespeed_timeout_seconds',
        label: 'API Timeout (seconds)',
        description: 'Timeout for Wavespeed API requests',
        type: 'number',
        min: 30,
        max: 600,
      },
      {
        key: 'wavespeed_min_balance',
        label: 'Min Balance Alert',
        description: 'Alert when Wavespeed balance falls below this amount',
        type: 'number',
        min: 0,
        step: '0.1',
      },
      {
        key: 'wavespeed_balance_cache_ttl_seconds',
        label: 'Balance Cache TTL (seconds)',
        description: 'How long to cache Wavespeed balance',
        type: 'number',
        min: 10,
        max: 600,
      },
    ],
  },
  {
    title: 'Cache & Performance',
    icon: Clock,
    fields: [
      {
        key: 'redis_cache_ttl_seconds',
        label: 'Default Cache TTL (seconds)',
        description: 'Default Redis cache time-to-live',
        type: 'number',
        min: 60,
        max: 3600,
      },
      {
        key: 'redis_active_generation_ttl_seconds',
        label: 'Active Generation TTL (seconds)',
        description: 'How long to keep active generation data',
        type: 'number',
        min: 300,
        max: 3600,
      },
    ],
  },
];

// --- Toast Notification ---

type ToastType = 'success' | 'error';

interface Toast {
  type: ToastType;
  message: string;
}

function ToastNotification({ toast, onDismiss }: { toast: Toast; onDismiss: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 4000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div
      className={cn(
        'fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-elevated animate-slide-in-up border',
        toast.type === 'success'
          ? 'bg-surface border-success/30 text-success'
          : 'bg-surface border-destructive/30 text-destructive',
      )}
    >
      {toast.type === 'success' ? (
        <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
      ) : (
        <XCircle className="w-5 h-5 flex-shrink-0" />
      )}
      <p className="text-sm font-medium">{toast.message}</p>
    </div>
  );
}

// --- Setting Input ---

function SettingInput({
  field,
  value,
  onChange,
}: {
  field: SettingFieldDef;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-6 py-3">
      <div className="sm:w-1/2">
        <label className="text-sm font-medium text-white">{field.label}</label>
        <p className="text-xs text-muted-foreground mt-0.5">{field.description}</p>
      </div>
      <div className="sm:w-1/2 sm:flex sm:justify-end">
        <input
          type={field.type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          min={field.min}
          step={field.step}
          className="w-full sm:w-40 bg-dark-400 border border-surface-lighter text-sm text-white rounded-lg px-3 py-2 focus-ring transition-colors hover:border-banana-500/30"
        />
      </div>
    </div>
  );
}

// --- Settings Section Card ---

function SettingSectionCard({
  section,
  values,
  onChange,
}: {
  section: SettingSectionDef;
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
}) {
  const Icon = section.icon;

  return (
    <div className="card-admin">
      <div className="px-5 py-4 border-b border-surface-lighter/50 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-accent-muted flex items-center justify-center">
          <Icon className="w-4 h-4 text-banana-500" />
        </div>
        <h3 className="text-sm font-semibold text-white">{section.title}</h3>
      </div>
      <div className="px-5 divide-y divide-surface-lighter/30">
        {section.fields.map((field) => (
          <SettingInput
            key={field.key}
            field={field}
            value={values[field.key] ?? ''}
            onChange={(v) => onChange(field.key, v)}
          />
        ))}
      </div>
    </div>
  );
}

// --- Loading Skeleton ---

function SettingsSkeleton() {
  return (
    <div className="space-y-6">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="card-admin">
          <div className="px-5 py-4 border-b border-surface-lighter/50 flex items-center gap-3">
            <div className="w-8 h-8 bg-surface-light rounded-lg animate-pulse-soft" />
            <div className="h-4 w-24 bg-surface-light rounded animate-pulse-soft" />
          </div>
          <div className="px-5 py-4 space-y-4">
            {Array.from({ length: i === 1 ? 3 : i === 2 ? 2 : 1 }).map((_, j) => (
              <div key={j} className="flex items-center gap-6">
                <div className="flex-1 space-y-1.5">
                  <div className="h-4 w-40 bg-surface-light rounded animate-pulse-soft" />
                  <div className="h-3 w-64 bg-surface-light rounded animate-pulse-soft" />
                </div>
                <div className="h-9 w-40 bg-surface-light rounded-lg animate-pulse-soft" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// --- Main Page ---

export function SettingsPage() {
  const queryClient = useQueryClient();
  const [localValues, setLocalValues] = useState<Record<string, string>>({});
  const [isDirty, setIsDirty] = useState(false);
  const [toast, setToast] = useState<Toast | null>(null);

  const settingsQuery = useQuery({
    queryKey: ['admin', 'settings'],
    queryFn: settingsApi.getSettings,
  });

  // Initialize local values when data is loaded
  useEffect(() => {
    if (settingsQuery.data) {
      const values: Record<string, string> = {};
      settingsQuery.data.forEach((s: SystemSetting) => {
        values[s.key] = s.value;
      });
      setLocalValues(values);
      setIsDirty(false);
    }
  }, [settingsQuery.data]);

  const saveMutation = useMutation({
    mutationFn: (settings: Record<string, string>) =>
      settingsApi.updateSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'settings'] });
      setIsDirty(false);
      setToast({ type: 'success', message: 'Settings saved successfully' });
    },
    onError: () => {
      setToast({ type: 'error', message: 'Failed to save settings. Please try again.' });
    },
  });

  const handleChange = useCallback((key: string, value: string) => {
    setLocalValues((prev) => ({ ...prev, [key]: value }));
    setIsDirty(true);
  }, []);

  const handleSave = useCallback(() => {
    // Only send changed values
    if (!settingsQuery.data) return;
    const original: Record<string, string> = {};
    settingsQuery.data.forEach((s: SystemSetting) => {
      original[s.key] = s.value;
    });

    const changed: Record<string, string> = {};
    for (const [key, value] of Object.entries(localValues)) {
      if (original[key] !== value) {
        changed[key] = value;
      }
    }

    if (Object.keys(changed).length === 0) {
      setIsDirty(false);
      return;
    }

    saveMutation.mutate(changed);
  }, [localValues, settingsQuery.data, saveMutation]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Settings</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Configure bot settings, pricing, referrals, and system limits.
          </p>
        </div>
        <button
          onClick={handleSave}
          disabled={!isDirty || saveMutation.isPending}
          className={cn(
            'btn-primary flex items-center gap-2',
            (!isDirty || saveMutation.isPending) && 'opacity-50 cursor-not-allowed',
          )}
        >
          {saveMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          Save Changes
        </button>
      </div>

      {/* Error banner */}
      {settingsQuery.isError && (
        <div className="flex items-center gap-3 bg-destructive-muted border border-destructive/30 text-destructive-foreground rounded-lg px-4 py-3">
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
          <p className="text-sm">Failed to load settings. Please try again.</p>
        </div>
      )}

      {/* Settings Sections */}
      {settingsQuery.isLoading ? (
        <SettingsSkeleton />
      ) : (
        <div className="space-y-6">
          {SETTING_SECTIONS.map((section) => (
            <SettingSectionCard
              key={section.title}
              section={section}
              values={localValues}
              onChange={handleChange}
            />
          ))}
        </div>
      )}

      {/* Unsaved Changes Bar */}
      {isDirty && (
        <div className="sticky bottom-6 z-40">
          <div className="flex items-center justify-between bg-dark-300 border border-banana-500/30 rounded-lg px-5 py-3 shadow-glow">
            <div className="flex items-center gap-2">
              <Settings className="w-4 h-4 text-banana-500" />
              <p className="text-sm text-white font-medium">You have unsaved changes</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  if (settingsQuery.data) {
                    const values: Record<string, string> = {};
                    settingsQuery.data.forEach((s: SystemSetting) => {
                      values[s.key] = s.value;
                    });
                    setLocalValues(values);
                    setIsDirty(false);
                  }
                }}
                className="btn-ghost text-sm"
              >
                Discard
              </button>
              <button
                onClick={handleSave}
                disabled={saveMutation.isPending}
                className="btn-primary text-sm flex items-center gap-2"
              >
                {saveMutation.isPending ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Save className="w-3.5 h-3.5" />
                )}
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <ToastNotification toast={toast} onDismiss={() => setToast(null)} />
      )}
    </div>
  );
}
