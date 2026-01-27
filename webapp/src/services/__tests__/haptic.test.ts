import { describe, it, expect, vi, beforeEach } from 'vitest';
import { haptic } from '../haptic';

describe('haptic service', () => {
  beforeEach(() => {
    // Reset window.Telegram before each test
    vi.stubGlobal('Telegram', undefined);
  });

  describe('impact', () => {
    it('calls impactOccurred when Telegram API is available', () => {
      const impactOccurred = vi.fn();
      vi.stubGlobal('Telegram', {
        WebApp: {
          HapticFeedback: {
            impactOccurred,
          },
        },
      });

      haptic.impact('light');

      expect(impactOccurred).toHaveBeenCalledWith('light');
    });

    it('does not throw when Telegram API is not available', () => {
      expect(() => haptic.impact('light')).not.toThrow();
    });
  });

  describe('notification', () => {
    it('calls notificationOccurred when Telegram API is available', () => {
      const notificationOccurred = vi.fn();
      vi.stubGlobal('Telegram', {
        WebApp: {
          HapticFeedback: {
            notificationOccurred,
          },
        },
      });

      haptic.notification('success');

      expect(notificationOccurred).toHaveBeenCalledWith('success');
    });

    it('does not throw when Telegram API is not available', () => {
      expect(() => haptic.notification('success')).not.toThrow();
    });
  });

  describe('selection', () => {
    it('calls selectionChanged when Telegram API is available', () => {
      const selectionChanged = vi.fn();
      vi.stubGlobal('Telegram', {
        WebApp: {
          HapticFeedback: {
            selectionChanged,
          },
        },
      });

      haptic.selection();

      expect(selectionChanged).toHaveBeenCalled();
    });

    it('does not throw when Telegram API is not available', () => {
      expect(() => haptic.selection()).not.toThrow();
    });
  });
});
