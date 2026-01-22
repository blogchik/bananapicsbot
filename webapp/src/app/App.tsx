import { AppProviders } from './providers'
import { AppRouter } from './Router'

export function App() {
  return (
    <AppProviders>
      <AppRouter />
    </AppProviders>
  )
}
