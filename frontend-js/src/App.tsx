import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Landing } from './pages/Landing';
import { Dashboard } from './pages/Dashboard';
import { CardDiscovery } from './pages/CardDiscovery';
import { IdentifyCards } from './pages/IdentifyCards';
import { Onboarding } from './pages/Onboarding';
import { BankManagement } from './pages/BankManagement';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import { useAuthStore } from './store/authStore';

function App() {
  const { isAuthenticated, user } = useAuthStore();

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            isAuthenticated ? (
              user?.onboarding_completed ? (
                <Navigate to="/dashboard" replace />
              ) : (
                <Navigate to="/onboarding" replace />
              )
            ) : (
              <Landing />
            )
          }
        />
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute requireOnboarding={false}>
              <Onboarding />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/cards/discover"
          element={
            <ProtectedRoute>
              <Layout>
                <CardDiscovery />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/cards/identify"
          element={
            <ProtectedRoute>
              <Layout>
                <IdentifyCards />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/banks/manage"
          element={
            <ProtectedRoute>
              <Layout>
                <BankManagement />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
