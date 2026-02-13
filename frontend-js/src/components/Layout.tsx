import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);
  
  // Auto-collapse sidebar on mobile
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setIsSidebarCollapsed(true);
      }
    };
    
    // Initial check
    handleResize();
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  // Auto-close sidebar when navigating on mobile
  useEffect(() => {
    if (window.innerWidth < 768) {
      setIsSidebarCollapsed(true);
    }
  }, [location.pathname]);

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
            <p>This dashboard shows your GetCardIQ insights:</p>
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
      {/* Mobile Menu Button - Only visible when sidebar is hidden on mobile */}
      {isSidebarCollapsed && (
        <button
          onClick={() => setIsSidebarCollapsed(false)}
          className="fixed top-4 left-4 z-40 md:hidden bg-purple-600 text-white p-3 rounded-full shadow-lg hover:bg-purple-700 transition-colors"
          aria-label="Open menu"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      )}

      {/* Overlay for mobile when sidebar is open */}
      {!isSidebarCollapsed && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={() => setIsSidebarCollapsed(true)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside className={`
        ${isSidebarCollapsed ? 'w-20' : 'w-64'}
        bg-white shadow-lg flex flex-col h-screen sticky top-0 transition-all duration-300
        ${isSidebarCollapsed ? 'hidden md:flex' : 'flex'}
        ${!isSidebarCollapsed && 'fixed md:sticky z-50 inset-y-0 left-0'}
      `}>
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          {/* Toggle Button */}
          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="mb-4 p-3 hover:bg-gray-100 rounded-lg transition-colors w-full flex items-center justify-center min-h-[44px] min-w-[44px]"
            title={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-label={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <span className="text-2xl">{isSidebarCollapsed ? '☰' : '✕'}</span>
          </button>
          
          {!isSidebarCollapsed && (
            <>
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
            </>
          )}
          
          {isSidebarCollapsed && (
            <button
              onClick={handleLogout}
              className="w-full p-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              title="Logout"
            >
              🚪
            </button>
          )}
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
                } ${isSidebarCollapsed ? 'text-center' : ''}`}
                title={isSidebarCollapsed ? 'My Dashboard' : ''}
              >
                {isSidebarCollapsed ? '🏠' : 'My Dashboard'}
              </Link>
            </li>
            <li>
              <Link
                to="/cards/identify"
                className={`block px-4 py-3 rounded-lg transition-colors ${
                  isActive('/cards/identify')
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold'
                    : 'text-gray-700 hover:bg-gray-100'
                } ${isSidebarCollapsed ? 'text-center' : ''}`}
                title={isSidebarCollapsed ? 'Identify My Cards' : ''}
              >
                {isSidebarCollapsed ? '🃏' : 'Identify My Cards'}
              </Link>
            </li>
            <li>
              <Link
                to="/cards/discover"
                className={`block px-4 py-3 rounded-lg transition-colors ${
                  isActive('/cards/discover')
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold'
                    : 'text-gray-700 hover:bg-gray-100'
                } ${isSidebarCollapsed ? 'text-center' : ''}`}
                title={isSidebarCollapsed ? 'Card Discovery' : ''}
              >
                {isSidebarCollapsed ? '🔍' : 'Card Discovery'}
              </Link>
            </li>
            <li>
              <Link
                to="/banks/manage"
                className={`block px-4 py-3 rounded-lg transition-colors ${
                  isActive('/banks/manage')
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold'
                    : 'text-gray-700 hover:bg-gray-100'
                } ${isSidebarCollapsed ? 'text-center' : ''}`}
                title={isSidebarCollapsed ? 'Manage Banks' : ''}
              >
                {isSidebarCollapsed ? '🏦' : 'Manage Banks'}
              </Link>
            </li>
          </ul>
        </nav>

        {/* Help Section */}
        {!isSidebarCollapsed && helpText && (
          <div className="p-4 border-t border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-2">{helpText.title}</h3>
            {helpText.content}
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main className={`flex-1 overflow-auto ${isSidebarCollapsed ? 'pt-16 md:pt-0' : ''}`}>
        {children}
      </main>
    </div>
  );
};
