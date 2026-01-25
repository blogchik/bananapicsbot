import { GenerationsPage } from './pages/GenerationsPage';
import { TelegramGate } from './components';
import { useTelegram } from './hooks/useTelegram';

/**
 * Main App component
 * Wraps the app with TelegramGate to ensure it's only accessible via Telegram
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

  // Authorized - show the main app
  return <GenerationsPage />;
}

export default App;
