import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const isActive = (path: string) => location.pathname === path;

  // Page-specific help text
  const getHelpText = () => {
    if (location.pathname === '/dashboard') {
      return {
        title: '💡 About',
        content: (
          <div className="text-sm text-gray-600 space-y-1">
            <p>This dashboard shows your credit card cashback optimization insights:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li><strong>Total Spent:</strong> Your transaction volume</li>
              <li><strong>Actual Rewards:</strong> Cashback you earned</li>
              <li><strong>Lost Savings:</strong> Opportunity cost from suboptimal card usage</li>
            </ul>
          </div>
        ),
      };
    } else if (location.pathname === '/cards/identify') {
      return {
        title: '💡 About Card Identification',
        content: (
          <div className="text-sm text-gray-600 space-y-1">
            <p>Link your Plaid-synced bank accounts to specific card products:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>We detect your credit cards from Plaid</li>
              <li>You tell us which product each card is</li>
              <li>We calculate accurate rewards based on real usage</li>
            </ul>
          </div>
        ),
      };
    }
    return null;
  };

  const helpText = getHelpText();

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-lg flex flex-col h-screen sticky top-0">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900 mb-4">🧭 Navigation</h2>
          
          {/* User Info */}
          <div className="mb-4">
            <p className="font-semibold text-gray-900">
              👤 {user?.name || user?.email}
            </p>
            <p className="text-sm text-gray-600">{user?.email}</p>
          </div>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
          >
            🚪 Logout
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 p-4 overflow-y-auto">
          <ul className="space-y-2">
            <li>
              <Link
                to="/dashboard"
                className={`block px-4 py-3 rounded-lg transition-colors ${
                  isActive('/dashboard')
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                My Dashboard
              </Link>
            </li>
            <li>
              <Link
                to="/cards/identify"
                className={`block px-4 py-3 rounded-lg transition-colors ${
                  isActive('/cards/identify')
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                Identify My Cards
              </Link>
            </li>
            <li>
              <Link
                to="/cards/discover"
                className={`block px-4 py-3 rounded-lg transition-colors ${
                  isActive('/cards/discover')
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                Card Discovery
              </Link>
            </li>
            <li>
              <Link
                to="/banks/manage"
                className={`block px-4 py-3 rounded-lg transition-colors ${
                  isActive('/banks/manage')
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                Manage Banks
              </Link>
            </li>
          </ul>
        </nav>

        {/* Help Section */}
        {helpText && (
          <div className="p-4 border-t border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-2">{helpText.title}</h3>
            {helpText.content}
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
};
