import { Outlet } from 'react-router-dom'
import { BottomNav } from './BottomNav'

export function AppLayout() {
  return (
    <div className="min-h-screen bg-tg-bg relative">
      {/* Background gradient mesh */}
      <div className="fixed inset-0 bg-gradient-mesh opacity-50 dark:opacity-30 pointer-events-none" />

      {/* Main content */}
      <main className="relative pb-24">
        <Outlet />
      </main>

      {/* Bottom navigation */}
      <BottomNav />
    </div>
  )
}
