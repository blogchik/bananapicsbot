import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  ArrowLeft,
  Users,
  MessageSquareText,
  Filter,
  Link2,
  Eye,
  AlertCircle,
  Check,
  Loader2,
} from 'lucide-react';
import { broadcastsApi, type CreateBroadcastInput } from '@/api/broadcasts';
import { cn } from '@/lib/utils';

// --- Constants ---

const FILTER_OPTIONS = [
  { value: 'all', label: 'All Users', description: 'Send to every registered user' },
  { value: 'active_7d', label: 'Active (7 days)', description: 'Users active in the last 7 days' },
  { value: 'active_30d', label: 'Active (30 days)', description: 'Users active in the last 30 days' },
  { value: 'with_balance', label: 'With Balance', description: 'Users who have credits remaining' },
  { value: 'paid_users', label: 'Paid Users', description: 'Users who made at least one purchase' },
  { value: 'new_users', label: 'New Users', description: 'Users who joined in the last 7 days' },
];

// --- Component ---

export function BroadcastCreatePage() {
  const navigate = useNavigate();

  // --- Form state ---
  const [contentType] = useState('text');
  const [text, setText] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [inlineButtonText, setInlineButtonText] = useState('');
  const [inlineButtonUrl, setInlineButtonUrl] = useState('');
  const [showPreview, setShowPreview] = useState(false);

  // --- Queries ---

  const usersCountQuery = useQuery({
    queryKey: ['admin', 'broadcasts', 'users-count', filterType],
    queryFn: () => broadcastsApi.getUsersCount(filterType),
    staleTime: 30_000,
  });

  // --- Mutation ---

  const createMutation = useMutation({
    mutationFn: (data: CreateBroadcastInput) => broadcastsApi.createBroadcast(data),
    onSuccess: () => {
      navigate('/broadcasts');
    },
  });

  // --- Validation ---

  const isTextValid = text.trim().length > 0;
  const isButtonValid =
    (!inlineButtonText && !inlineButtonUrl) ||
    (inlineButtonText.trim().length > 0 && isValidUrl(inlineButtonUrl));
  const isFormValid = isTextValid && isButtonValid;

  function isValidUrl(url: string): boolean {
    if (!url) return false;
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  }

  // --- Handlers ---

  function handleSubmit() {
    if (!isFormValid) return;

    const data: CreateBroadcastInput = {
      content_type: contentType,
      text: text.trim(),
      filter_type: filterType,
    };

    if (inlineButtonText.trim() && inlineButtonUrl.trim()) {
      data.inline_button_text = inlineButtonText.trim();
      data.inline_button_url = inlineButtonUrl.trim();
    }

    createMutation.mutate(data);
  }

  // Auto-show preview when text is long enough
  useEffect(() => {
    if (text.length > 10 && !showPreview) {
      setShowPreview(true);
    }
  }, [text, showPreview]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/broadcasts')}
          className="w-9 h-9 rounded-lg bg-surface-light flex items-center justify-center hover:bg-surface-lighter transition-colors"
        >
          <ArrowLeft className="w-4 h-4 text-muted-foreground" />
        </button>
        <div>
          <h2 className="text-2xl font-bold text-white">New Broadcast</h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Create and send a new broadcast message.
          </p>
        </div>
      </div>

      {/* Error */}
      {createMutation.isError && (
        <div className="flex items-center gap-3 bg-destructive-muted border border-destructive/30 text-destructive-foreground rounded-lg px-4 py-3">
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
          <p className="text-sm">Failed to create broadcast. Please try again.</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Step 1: Content Type */}
          <div className="card-admin p-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-full bg-banana-500 text-dark-500 flex items-center justify-center text-xs font-bold">1</div>
              <h3 className="text-sm font-semibold text-white">Content Type</h3>
            </div>
            <div className="flex gap-3">
              <button
                className={cn(
                  'flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors border',
                  contentType === 'text'
                    ? 'bg-accent-muted border-banana-500/30 text-banana-500'
                    : 'bg-surface border-surface-lighter/50 text-muted-foreground hover:text-white hover:border-banana-500/20',
                )}
              >
                <MessageSquareText className="w-4 h-4" />
                Text Message
              </button>
            </div>
          </div>

          {/* Step 2: Message Text */}
          <div className="card-admin p-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-full bg-banana-500 text-dark-500 flex items-center justify-center text-xs font-bold">2</div>
              <h3 className="text-sm font-semibold text-white">Message</h3>
            </div>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Type your broadcast message here...&#10;&#10;You can use multiple lines and Telegram formatting."
              rows={6}
              className="w-full bg-surface border border-surface-lighter/50 rounded-lg px-4 py-3 text-sm text-white placeholder:text-muted focus-ring hover:border-banana-500/30 transition-colors resize-y min-h-[120px]"
            />
            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-muted-foreground">
                Supports Telegram HTML formatting (bold, italic, links, etc.)
              </p>
              <span className={cn('text-xs', text.length > 4000 ? 'text-destructive' : 'text-muted-foreground')}>
                {text.length} / 4096
              </span>
            </div>
          </div>

          {/* Step 3: Target Audience */}
          <div className="card-admin p-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-full bg-banana-500 text-dark-500 flex items-center justify-center text-xs font-bold">3</div>
              <h3 className="text-sm font-semibold text-white">Target Audience</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {FILTER_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setFilterType(option.value)}
                  className={cn(
                    'flex items-start gap-3 p-3 rounded-lg text-left transition-colors border',
                    filterType === option.value
                      ? 'bg-accent-muted border-banana-500/30'
                      : 'bg-surface border-surface-lighter/50 hover:border-banana-500/20',
                  )}
                >
                  <Filter
                    className={cn(
                      'w-4 h-4 mt-0.5 flex-shrink-0',
                      filterType === option.value ? 'text-banana-500' : 'text-muted',
                    )}
                  />
                  <div>
                    <p
                      className={cn(
                        'text-sm font-medium',
                        filterType === option.value ? 'text-banana-500' : 'text-white',
                      )}
                    >
                      {option.label}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">{option.description}</p>
                  </div>
                </button>
              ))}
            </div>

            {/* Recipient count */}
            <div className="mt-4 flex items-center gap-2 px-3 py-2.5 bg-surface-light/50 rounded-lg">
              <Users className="w-4 h-4 text-banana-500" />
              {usersCountQuery.isLoading ? (
                <span className="text-sm text-muted-foreground flex items-center gap-1.5">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Counting recipients...
                </span>
              ) : usersCountQuery.isError ? (
                <span className="text-sm text-muted-foreground">Unable to fetch recipient count</span>
              ) : (
                <span className="text-sm text-white">
                  <span className="font-semibold text-banana-500">
                    {(usersCountQuery.data?.count ?? 0).toLocaleString()}
                  </span>
                  {' '}recipients will receive this broadcast
                </span>
              )}
            </div>
          </div>

          {/* Step 4: Inline Button (optional) */}
          <div className="card-admin p-6">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-6 h-6 rounded-full bg-surface-light text-muted-foreground flex items-center justify-center text-xs font-bold">4</div>
              <h3 className="text-sm font-semibold text-white">Inline Button</h3>
              <span className="text-xs text-muted-foreground ml-1">(optional)</span>
            </div>
            <p className="text-xs text-muted-foreground mb-4 ml-8">
              Add a clickable button below the message.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-muted-foreground mb-1.5">Button Text</label>
                <input
                  type="text"
                  value={inlineButtonText}
                  onChange={(e) => setInlineButtonText(e.target.value)}
                  placeholder="e.g. Visit Website"
                  className="w-full bg-surface border border-surface-lighter/50 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-muted focus-ring hover:border-banana-500/30 transition-colors"
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1.5">Button URL</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                    <Link2 className="w-3.5 h-3.5 text-muted" />
                  </div>
                  <input
                    type="url"
                    value={inlineButtonUrl}
                    onChange={(e) => setInlineButtonUrl(e.target.value)}
                    placeholder="https://example.com"
                    className="w-full bg-surface border border-surface-lighter/50 rounded-lg pl-9 pr-3 py-2.5 text-sm text-white placeholder:text-muted focus-ring hover:border-banana-500/30 transition-colors"
                  />
                </div>
              </div>
            </div>

            {/* Validation message for button */}
            {inlineButtonText && !inlineButtonUrl && (
              <p className="text-xs text-warning mt-2 ml-0.5">
                Please provide a URL for the button.
              </p>
            )}
            {inlineButtonUrl && !isValidUrl(inlineButtonUrl) && (
              <p className="text-xs text-destructive mt-2 ml-0.5">
                Please enter a valid URL (e.g. https://example.com).
              </p>
            )}
          </div>

          {/* Submit */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/broadcasts')}
              className="btn-ghost"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!isFormValid || createMutation.isPending}
              className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  Create Broadcast
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right: Preview */}
        <div className="lg:col-span-1">
          <div className="card-admin p-6 sticky top-6">
            <div className="flex items-center gap-2 mb-4">
              <Eye className="w-4 h-4 text-banana-500" />
              <h3 className="text-sm font-semibold text-white">Preview</h3>
            </div>

            {/* Message preview */}
            <div className="bg-dark-300 rounded-lg p-4 min-h-[200px]">
              {text.trim() ? (
                <div className="space-y-3">
                  {/* Simulated Telegram message bubble */}
                  <div className="bg-surface-light rounded-xl rounded-tl-sm p-3 max-w-full">
                    <p className="text-sm text-white whitespace-pre-wrap break-words leading-relaxed">
                      {text}
                    </p>
                  </div>

                  {/* Inline button preview */}
                  {inlineButtonText && (
                    <div className="flex justify-center">
                      <span className="inline-flex items-center gap-1.5 px-4 py-2 bg-info/20 text-info text-sm font-medium rounded-lg border border-info/30">
                        {inlineButtonText}
                        {inlineButtonUrl && <Link2 className="w-3.5 h-3.5" />}
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-[160px] text-center">
                  <MessageSquareText className="w-8 h-8 text-muted mb-2" />
                  <p className="text-xs text-muted-foreground">
                    Start typing to see a preview of your message.
                  </p>
                </div>
              )}
            </div>

            {/* Summary */}
            <div className="mt-4 space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Content Type</span>
                <span className="text-white font-medium capitalize">{contentType}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Target</span>
                <span className="text-white font-medium">
                  {FILTER_OPTIONS.find((f) => f.value === filterType)?.label ?? filterType}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Recipients</span>
                <span className="text-banana-500 font-semibold">
                  {usersCountQuery.isLoading
                    ? '...'
                    : (usersCountQuery.data?.count ?? 0).toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Message Length</span>
                <span className={cn('font-medium', text.length > 4000 ? 'text-destructive' : 'text-white')}>
                  {text.length} chars
                </span>
              </div>
              {inlineButtonText && (
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Button</span>
                  <span className="text-white font-medium truncate max-w-[140px]">{inlineButtonText}</span>
                </div>
              )}
            </div>

            {/* Validation summary */}
            <div className="mt-4 space-y-1.5">
              <ValidationItem valid={isTextValid} label="Message text is provided" />
              <ValidationItem valid={isButtonValid} label="Inline button is valid (or empty)" />
              <ValidationItem
                valid={text.length <= 4096}
                label="Message within 4096 char limit"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- Validation indicator ---

function ValidationItem({ valid, label }: { valid: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <div
        className={cn(
          'w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0',
          valid ? 'bg-success-muted' : 'bg-surface-light',
        )}
      >
        {valid ? (
          <Check className="w-2.5 h-2.5 text-success" />
        ) : (
          <div className="w-1.5 h-1.5 rounded-full bg-muted" />
        )}
      </div>
      <span className={cn(valid ? 'text-muted-foreground' : 'text-muted')}>{label}</span>
    </div>
  );
}
