import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LoginPage } from '@/pages/LoginPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { UsersListPage } from '@/pages/users/UsersListPage';
import { UserDetailPage } from '@/pages/users/UserDetailPage';
import { BroadcastsListPage } from '@/pages/broadcasts/BroadcastsListPage';
import { BroadcastCreatePage } from '@/pages/broadcasts/BroadcastCreatePage';
import { ModelsPage } from '@/pages/models/ModelsPage';
import { PaymentsPage } from '@/pages/payments/PaymentsPage';
import { GenerationsPage } from '@/pages/generations/GenerationsPage';
import { SettingsPage } from '@/pages/settings/SettingsPage';
import { AppLayout } from '@/components/layout/AppLayout';
import { AuthGuard } from '@/components/layout/AuthGuard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <AuthGuard>
                <AppLayout />
              </AuthGuard>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="users" element={<UsersListPage />} />
            <Route path="users/:id" element={<UserDetailPage />} />
            <Route path="broadcasts" element={<BroadcastsListPage />} />
            <Route path="broadcasts/new" element={<BroadcastCreatePage />} />
            <Route path="models" element={<ModelsPage />} />
            <Route path="payments" element={<PaymentsPage />} />
            <Route path="generations" element={<GenerationsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
