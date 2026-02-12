import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Check,
  X,
  Pencil,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { modelsApi, type ModelCatalog } from '@/api/models';

// --- Capability Badge ---

function CapabilityBadge({ label, active }: { label: string; active: boolean }) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide',
        active
          ? 'bg-banana-500/15 text-banana-400 border border-banana-500/25'
          : 'bg-surface-light/50 text-muted border border-surface-lighter/30',
      )}
    >
      {label}
    </span>
  );
}

// --- Status Toggle ---

function StatusToggle({
  isActive,
  loading,
  onToggle,
}: {
  isActive: boolean;
  loading: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      disabled={loading}
      className={cn(
        'relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus-ring',
        isActive ? 'bg-success' : 'bg-surface-lighter',
        loading && 'opacity-50 cursor-not-allowed',
      )}
    >
      <span
        className={cn(
          'inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200',
          isActive ? 'translate-x-6' : 'translate-x-1',
        )}
      />
    </button>
  );
}

// --- Inline Price Editor ---

function InlinePriceEditor({
  modelId,
  currentPrice,
}: {
  modelId: number;
  currentPrice: number;
}) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(String(currentPrice));
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (unitPrice: number) =>
      modelsApi.updateModelPrice(modelId, { unit_price: unitPrice }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'models'] });
      setEditing(false);
    },
  });

  const handleSave = useCallback(() => {
    const numValue = parseFloat(value);
    if (isNaN(numValue) || numValue < 0) return;
    mutation.mutate(numValue);
  }, [value, mutation]);

  const handleCancel = useCallback(() => {
    setValue(String(currentPrice));
    setEditing(false);
  }, [currentPrice]);

  if (!editing) {
    return (
      <button
        onClick={() => setEditing(true)}
        className="group/price flex items-center gap-1.5 text-sm text-white hover:text-banana-400 transition-colors"
      >
        <span className="font-medium">{currentPrice}</span>
        <Pencil className="w-3 h-3 opacity-0 group-hover/price:opacity-100 transition-opacity" />
      </button>
    );
  }

  return (
    <div className="flex items-center gap-1.5">
      <input
        type="number"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') handleSave();
          if (e.key === 'Escape') handleCancel();
        }}
        autoFocus
        min={0}
        step="0.01"
        className="w-20 bg-dark-400 border border-surface-lighter text-sm text-white rounded px-2 py-1 focus-ring"
      />
      <button
        onClick={handleSave}
        disabled={mutation.isPending}
        className="p-1 rounded hover:bg-success/20 text-success transition-colors"
      >
        {mutation.isPending ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <Check className="w-3.5 h-3.5" />
        )}
      </button>
      <button
        onClick={handleCancel}
        className="p-1 rounded hover:bg-destructive/20 text-destructive transition-colors"
      >
        <X className="w-3.5 h-3.5" />
      </button>
      {mutation.isError && (
        <span className="text-xs text-destructive ml-1">Failed</span>
      )}
    </div>
  );
}

// --- Model Row ---

function ModelRow({ model }: { model: ModelCatalog }) {
  const queryClient = useQueryClient();

  const toggleMutation = useMutation({
    mutationFn: () =>
      modelsApi.updateModel(model.id, { is_active: !model.is_active }),
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ['admin', 'models'] });
      const previous = queryClient.getQueryData<ModelCatalog[]>(['admin', 'models']);
      queryClient.setQueryData<ModelCatalog[]>(['admin', 'models'], (old) =>
        old?.map((m) =>
          m.id === model.id ? { ...m, is_active: !m.is_active } : m,
        ),
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['admin', 'models'], context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'models'] });
    },
  });

  const activePrice = model.prices.find((p) => p.is_active);
  const price = activePrice?.unit_price ?? 0;

  return (
    <tr className="border-b border-surface-lighter/30 hover:bg-surface-light/30 transition-colors">
      <td className="px-4 py-3">
        <div>
          <p className="text-sm font-medium text-white">{model.name}</p>
          <p className="text-xs text-muted-foreground font-mono">{model.key}</p>
        </div>
      </td>
      <td className="px-4 py-3">
        <span className="text-sm text-muted-foreground">{model.provider}</span>
      </td>
      <td className="px-4 py-3">
        <InlinePriceEditor modelId={model.id} currentPrice={price} />
      </td>
      <td className="px-4 py-3">
        <div className="flex flex-wrap gap-1">
          <CapabilityBadge label="T2I" active={model.supports_text_to_image} />
          <CapabilityBadge label="I2I" active={model.supports_image_to_image} />
          <CapabilityBadge label="Ref" active={model.supports_reference} />
          <CapabilityBadge label="AR" active={model.supports_aspect_ratio} />
          <CapabilityBadge label="Style" active={model.supports_style} />
        </div>
      </td>
      <td className="px-4 py-3">
        <StatusToggle
          isActive={model.is_active}
          loading={toggleMutation.isPending}
          onToggle={() => toggleMutation.mutate()}
        />
      </td>
    </tr>
  );
}

// --- Table Skeleton ---

function TableSkeleton() {
  return (
    <>
      {Array.from({ length: 5 }).map((_, i) => (
        <tr key={i} className="border-b border-surface-lighter/30">
          <td className="px-4 py-3">
            <div className="space-y-1.5">
              <div className="h-4 w-32 bg-surface-light rounded animate-pulse-soft" />
              <div className="h-3 w-24 bg-surface-light rounded animate-pulse-soft" />
            </div>
          </td>
          <td className="px-4 py-3">
            <div className="h-4 w-20 bg-surface-light rounded animate-pulse-soft" />
          </td>
          <td className="px-4 py-3">
            <div className="h-4 w-12 bg-surface-light rounded animate-pulse-soft" />
          </td>
          <td className="px-4 py-3">
            <div className="flex gap-1">
              {Array.from({ length: 4 }).map((_, j) => (
                <div
                  key={j}
                  className="h-5 w-8 bg-surface-light rounded animate-pulse-soft"
                />
              ))}
            </div>
          </td>
          <td className="px-4 py-3">
            <div className="h-6 w-11 bg-surface-light rounded-full animate-pulse-soft" />
          </td>
        </tr>
      ))}
    </>
  );
}

// --- Main Page ---

export function ModelsPage() {
  const modelsQuery = useQuery({
    queryKey: ['admin', 'models'],
    queryFn: modelsApi.getModels,
  });

  const models = modelsQuery.data ?? [];
  const activeCount = models.filter((m) => m.is_active).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Models</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Manage AI generation models, pricing, and availability.
          </p>
        </div>
        {!modelsQuery.isLoading && (
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>
              {activeCount} active / {models.length} total
            </span>
          </div>
        )}
      </div>

      {/* Error banner */}
      {modelsQuery.isError && (
        <div className="flex items-center gap-3 bg-destructive-muted border border-destructive/30 text-destructive-foreground rounded-lg px-4 py-3">
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
          <p className="text-sm">Failed to load models. Please try again.</p>
        </div>
      )}

      {/* Table */}
      <div className="card-admin overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-surface-lighter/50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Model
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Provider
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Price (credits)
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Capabilities
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {modelsQuery.isLoading ? (
                <TableSkeleton />
              ) : models.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center">
                    <div className="flex flex-col items-center">
                      <div className="w-12 h-12 rounded-xl bg-accent-muted flex items-center justify-center mb-3">
                        <Box className="w-6 h-6 text-banana-500" />
                      </div>
                      <p className="text-sm text-muted-foreground">
                        No models found
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                models.map((model) => (
                  <ModelRow key={model.id} model={model} />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
