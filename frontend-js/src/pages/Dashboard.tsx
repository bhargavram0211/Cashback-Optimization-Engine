import React from 'react';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                💳 Cashback Optimization Dashboard
              </h1>
              <p className="text-gray-600 mt-2">
                Welcome, {user?.name || user?.email}!
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Dashboard Placeholder</h2>
          <p className="text-gray-600">
            This is a protected route. The full dashboard will be implemented in Part 2.
          </p>
          <p className="text-gray-600 mt-2">
            User ID: {user?.id}
          </p>
          <p className="text-gray-600">
            Onboarding Completed: {user?.onboarding_completed ? 'Yes' : 'No'}
          </p>
        </div>
      </div>
    </div>
  );
};
