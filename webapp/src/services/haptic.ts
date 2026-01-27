/**
 * Haptic feedback service
 * Centralized access to Telegram WebApp haptic feedback
 */

export const haptic = {
  /**
   * Trigger impact haptic feedback
   * @param style - Impact style: 'light', 'medium', or 'heavy'
   */
  impact: (style: 'light' | 'medium' | 'heavy' = 'light') => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred(style);
  },

  /**
   * Trigger notification haptic feedback
   * @param type - Notification type: 'success', 'error', or 'warning'
   */
  notification: (type: 'success' | 'error' | 'warning') => {
    window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred(type);
  },

  /**
   * Trigger selection changed haptic feedback
   */
  selection: () => {
    window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
  },
};
