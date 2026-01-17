import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Landing } from './pages/Landing';
import { Dashboard } from './pages/Dashboard';
import { CardDiscovery } from './pages/CardDiscovery';
import { IdentifyCards } from './pages/IdentifyCards';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import { useAuthStore } from './store/authStore';

function App() {
  const { isAuthenticated } = useAuthStore();

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <Landing />
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
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
