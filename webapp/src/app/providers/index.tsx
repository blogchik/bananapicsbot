import { type ReactNode } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { TelegramProvider } from './TelegramProvider'
import { QueryProvider } from './QueryProvider'

interface AppProvidersProps {
  children: ReactNode
}

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <BrowserRouter>
      <TelegramProvider>
        <QueryProvider>
          {children}
        </QueryProvider>
      </TelegramProvider>
    </BrowserRouter>
  )
}

export { useTelegramContext } from './TelegramProvider'
