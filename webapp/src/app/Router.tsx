import { Routes, Route } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import { AppLayout } from '@/shared/components/layout/AppLayout'
import { PageLoader } from '@/shared/components/ui/PageLoader'

// Lazy load pages for better performance
const HomePage = lazy(() => import('@/pages/HomePage'))
const GeneratePage = lazy(() => import('@/pages/GeneratePage'))
const GalleryPage = lazy(() => import('@/pages/GalleryPage'))
const ToolsPage = lazy(() => import('@/pages/ToolsPage'))
const WalletPage = lazy(() => import('@/pages/WalletPage'))
const ReferralPage = lazy(() => import('@/pages/ReferralPage'))
const SettingsPage = lazy(() => import('@/pages/SettingsPage'))

export function AppRouter() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route
          index
          element={
            <Suspense fallback={<PageLoader />}>
              <HomePage />
            </Suspense>
          }
        />
        <Route
          path="generate"
          element={
            <Suspense fallback={<PageLoader />}>
              <GeneratePage />
            </Suspense>
          }
        />
        <Route
          path="gallery"
          element={
            <Suspense fallback={<PageLoader />}>
              <GalleryPage />
            </Suspense>
          }
        />
        <Route
          path="tools"
          element={
            <Suspense fallback={<PageLoader />}>
              <ToolsPage />
            </Suspense>
          }
        />
        <Route
          path="wallet"
          element={
            <Suspense fallback={<PageLoader />}>
              <WalletPage />
            </Suspense>
          }
        />
        <Route
          path="referral"
          element={
            <Suspense fallback={<PageLoader />}>
              <ReferralPage />
            </Suspense>
          }
        />
        <Route
          path="settings"
          element={
            <Suspense fallback={<PageLoader />}>
              <SettingsPage />
            </Suspense>
          }
        />
      </Route>
    </Routes>
  )
}
