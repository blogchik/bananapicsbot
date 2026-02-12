import { useEffect, useRef } from 'react';
import { AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'default' | 'destructive';
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  loading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    if (!open) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && !loading) {
        onCancel();
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, loading, onCancel]);

  // Prevent body scroll when open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={(e) => {
        if (e.target === overlayRef.current && !loading) {
          onCancel();
        }
      }}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in" />

      {/* Dialog */}
      <div className="relative card-admin p-6 w-full max-w-md animate-slide-in-up shadow-elevated">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div
            className={cn(
              'w-10 h-10 rounded-lg flex-shrink-0 flex items-center justify-center',
              variant === 'destructive' ? 'bg-destructive-muted' : 'bg-accent-muted',
            )}
          >
            <AlertTriangle
              className={cn(
                'w-5 h-5',
                variant === 'destructive' ? 'text-destructive' : 'text-banana-500',
              )}
            />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-white">{title}</h3>
            <p className="text-sm text-muted-foreground mt-1.5 leading-relaxed">
              {description}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 mt-6">
          <button
            onClick={onCancel}
            disabled={loading}
            className="btn-ghost text-sm disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-semibold transition-colors duration-150 disabled:opacity-50',
              variant === 'destructive'
                ? 'bg-destructive text-white hover:bg-red-600 active:bg-red-700'
                : 'btn-primary',
            )}
          >
            {loading ? (
              <span className="inline-flex items-center gap-2">
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Processing...
              </span>
            ) : (
              confirmLabel
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
