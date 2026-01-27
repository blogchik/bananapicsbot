import { GenerationsPage } from './pages/GenerationsPage';
import { TelegramGate } from './components';
import { useTelegram } from './hooks/useTelegram';
import { I18nProvider } from './contexts/I18nContext';

/**
 * Main App component
 * Wraps the app with I18nProvider and TelegramGate
 */
function App() {
  const { isReady, isAuthorized } = useTelegram();

  // Show nothing while checking authorization
  if (!isReady) {
    return (
      <div className="fixed inset-0 bg-dark-500 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-banana-500/20 border-t-banana-500 rounded-full animate-spin" />
      </div>
    );
  }

  // Show blocked screen if not authorized (not opened via Telegram)
  if (!isAuthorized) {
    return <TelegramGate />;
  }

  // Authorized - wrap main app with I18nProvider
  return (
    <I18nProvider>
      <GenerationsPage />
    </I18nProvider>
  );
}

export default App;
