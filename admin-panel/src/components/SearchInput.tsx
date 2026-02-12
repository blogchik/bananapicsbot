import { useState, useEffect, useRef } from 'react';
import { Search, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SearchInputProps {
  placeholder?: string;
  value?: string;
  onChange: (value: string) => void;
  debounceMs?: number;
  className?: string;
}

export function SearchInput({
  placeholder = 'Search...',
  value: externalValue,
  onChange,
  debounceMs = 300,
  className,
}: SearchInputProps) {
  const [localValue, setLocalValue] = useState(externalValue ?? '');
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isControlled = externalValue !== undefined;

  // Sync external value changes
  useEffect(() => {
    if (isControlled) {
      setLocalValue(externalValue);
    }
  }, [externalValue, isControlled]);

  function handleChange(newValue: string) {
    setLocalValue(newValue);

    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    timerRef.current = setTimeout(() => {
      onChange(newValue);
    }, debounceMs);
  }

  function handleClear() {
    setLocalValue('');
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    onChange('');
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  return (
    <div className={cn('relative', className)}>
      <div className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none">
        <Search className="w-4 h-4 text-muted" />
      </div>
      <input
        type="text"
        value={localValue}
        onChange={(e) => handleChange(e.target.value)}
        placeholder={placeholder}
        className={cn(
          'w-full bg-surface border border-surface-lighter/50 rounded-lg',
          'pl-10 pr-10 py-2.5 text-sm text-white',
          'placeholder:text-muted',
          'focus-ring',
          'hover:border-banana-500/30 transition-colors duration-150',
        )}
      />
      {localValue && (
        <button
          onClick={handleClear}
          className="absolute inset-y-0 right-0 flex items-center pr-3 text-muted hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
