/**
 * WebApp Logger
 * Centralized logging for all WebApp data and events
 * Logs are sent to browser console and can be configured to send to backend
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  category: string;
  message: string;
  data?: unknown;
}

// Enable/disable logging based on environment
const IS_DEV = import.meta.env.DEV;
const LOG_ENABLED = IS_DEV || import.meta.env.VITE_ENABLE_LOGGING === 'true';

// Color codes for different log levels
const LOG_COLORS: Record<LogLevel, string> = {
  debug: '#888',
  info: '#2196F3',
  warn: '#FF9800',
  error: '#F44336',
};

// Category colors
const CATEGORY_COLORS: Record<string, string> = {
  telegram: '#0088cc',
  api: '#4CAF50',
  event: '#9C27B0',
  user: '#FF5722',
  generation: '#00BCD4',
  ui: '#795548',
};

function formatLog(entry: LogEntry): void {
  if (!LOG_ENABLED) return;

  const categoryColor = CATEGORY_COLORS[entry.category] || '#666';
  const levelColor = LOG_COLORS[entry.level];

  const styles = [
    `color: ${categoryColor}; font-weight: bold;`,
    `color: ${levelColor};`,
    'color: inherit;',
  ];

  const prefix = `[${entry.timestamp}] [%c${entry.category.toUpperCase()}%c] [${entry.level.toUpperCase()}%c]`;

  if (entry.data !== undefined) {
    console.groupCollapsed(prefix, ...styles, entry.message);
    console.log('Data:', entry.data);
    console.groupEnd();
  } else {
    console.log(prefix, ...styles, entry.message);
  }
}

function createLogEntry(
  level: LogLevel,
  category: string,
  message: string,
  data?: unknown
): LogEntry {
  return {
    timestamp: new Date().toISOString().substring(11, 23),
    level,
    category,
    message,
    data,
  };
}

/**
 * Logger instance for different categories
 */
export const logger = {
  // Telegram WebApp events
  telegram: {
    debug: (message: string, data?: unknown) =>
      formatLog(createLogEntry('debug', 'telegram', message, data)),
    info: (message: string, data?: unknown) =>
      formatLog(createLogEntry('info', 'telegram', message, data)),
    warn: (message: string, data?: unknown) =>
      formatLog(createLogEntry('warn', 'telegram', message, data)),
    error: (message: string, data?: unknown) =>
      formatLog(createLogEntry('error', 'telegram', message, data)),
  },

  // API calls
  api: {
    debug: (message: string, data?: unknown) =>
      formatLog(createLogEntry('debug', 'api', message, data)),
    info: (message: string, data?: unknown) =>
      formatLog(createLogEntry('info', 'api', message, data)),
    warn: (message: string, data?: unknown) =>
      formatLog(createLogEntry('warn', 'api', message, data)),
    error: (message: string, data?: unknown) =>
      formatLog(createLogEntry('error', 'api', message, data)),
  },

  // WebApp events (viewport, theme, etc.)
  event: {
    debug: (message: string, data?: unknown) =>
      formatLog(createLogEntry('debug', 'event', message, data)),
    info: (message: string, data?: unknown) =>
      formatLog(createLogEntry('info', 'event', message, data)),
    warn: (message: string, data?: unknown) =>
      formatLog(createLogEntry('warn', 'event', message, data)),
    error: (message: string, data?: unknown) =>
      formatLog(createLogEntry('error', 'event', message, data)),
  },

  // User-related logs
  user: {
    debug: (message: string, data?: unknown) =>
      formatLog(createLogEntry('debug', 'user', message, data)),
    info: (message: string, data?: unknown) =>
      formatLog(createLogEntry('info', 'user', message, data)),
    warn: (message: string, data?: unknown) =>
      formatLog(createLogEntry('warn', 'user', message, data)),
    error: (message: string, data?: unknown) =>
      formatLog(createLogEntry('error', 'user', message, data)),
  },

  // Generation-related logs
  generation: {
    debug: (message: string, data?: unknown) =>
      formatLog(createLogEntry('debug', 'generation', message, data)),
    info: (message: string, data?: unknown) =>
      formatLog(createLogEntry('info', 'generation', message, data)),
    warn: (message: string, data?: unknown) =>
      formatLog(createLogEntry('warn', 'generation', message, data)),
    error: (message: string, data?: unknown) =>
      formatLog(createLogEntry('error', 'generation', message, data)),
  },

  // UI interactions
  ui: {
    debug: (message: string, data?: unknown) =>
      formatLog(createLogEntry('debug', 'ui', message, data)),
    info: (message: string, data?: unknown) =>
      formatLog(createLogEntry('info', 'ui', message, data)),
    warn: (message: string, data?: unknown) =>
      formatLog(createLogEntry('warn', 'ui', message, data)),
    error: (message: string, data?: unknown) =>
      formatLog(createLogEntry('error', 'ui', message, data)),
  },
};

export default logger;
