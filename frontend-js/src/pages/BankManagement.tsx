import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { plaidAPI, itemsAPI, syncAPI } from '../api/client';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { PlaidLink, getPlaidExitErrorMessage } from '../components/PlaidLink';
import { SESSION_EXPIRED_MESSAGE } from '../constants/errors';
import type { PlaidItemResponse, PlaidLinkOnSuccessMetadata, PlaidLinkOnExitMetadata } from '../types';

export const BankManagement: React.FC = () => {
  const { user } = useAuthStore();
  const [plaidItems, setPlaidItems] = useState<PlaidItemResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Plaid Link state
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [isCreatingLinkToken, setIsCreatingLinkToken] = useState(false);
  const [removingItemId, setRemovingItemId] = useState<string | null>(null);
  const [syncingItemId, setSyncingItemId] = useState<string | null>(null);

  // Fetch PlaidItems on mount
  useEffect(() => {
    if (user?.id) {
      fetchPlaidItems();
    }
  }, [user?.id]);

  const fetchPlaidItems = async () => {
    if (!user?.id) return;

    setIsLoading(true);
    setError(null);

    try {
      const items = await itemsAPI.getUserPlaidItems();
      setPlaidItems(items);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to load connected banks';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateLinkToken = async () => {
    setIsCreatingLinkToken(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await plaidAPI.createLinkToken();
      setLinkToken(response.link_token);
    } catch (err: any) {
      // Handle 401 by showing error and redirecting
      if (err.response?.status === 401) {
        setError(SESSION_EXPIRED_MESSAGE);
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
        setIsCreatingLinkToken(false);
        return;
      }
      
      const errorMessage = err.response?.data?.detail || 'Failed to create Plaid Link token';
      setError(errorMessage);
      setIsCreatingLinkToken(false);
    }
  };

  const handlePlaidSuccess = async (publicToken: string, metadata: PlaidLinkOnSuccessMetadata) => {
    setError(null);
    setSuccessMessage(null);
    setIsCreatingLinkToken(false);

    try {
      const response = await plaidAPI.exchangeToken({
        public_token: publicToken,
        institution_id: metadata.institution.institution_id,
        institution_name: metadata.institution.name,
      });

      setSuccessMessage(
        `✅ Successfully connected to ${response.institution_name}\n` +
        `📊 Synced ${response.transactions_synced} transactions\n` +
        `💳 Found ${response.cards_found} credit card(s)`
      );

      // Refresh PlaidItems list
      await fetchPlaidItems();

      // Reset link token
      setLinkToken(null);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to exchange token';
      setError(errorMessage);
      setLinkToken(null);
    }
  };

  const handlePlaidExit = (err: Error | null, metadata: PlaidLinkOnExitMetadata | null) => {
    setIsCreatingLinkToken(false);
    setLinkToken(null);

    if (err || metadata) {
      const errorMessage = getPlaidExitErrorMessage(err, metadata);
      setError(errorMessage);
    }
  };

  const handleRemoveBank = async (itemId: string) => {
    if (!confirm('Are you sure you want to remove this bank connection? This will stop syncing transactions from this bank.')) {
      return;
    }

    setRemovingItemId(itemId);
    setError(null);
    setSuccessMessage(null);

    try {
      await itemsAPI.deletePlaidItem(itemId);
      setSuccessMessage('Bank connection removed successfully');
      // Refresh the list after a short delay to ensure UI updates
      setTimeout(async () => {
        await fetchPlaidItems();
      }, 100);
    } catch (err: any) {
      // Handle 401 by redirecting to login
      if (err.response?.status === 401) {
        setError(SESSION_EXPIRED_MESSAGE);
        // Redirect after a short delay to show the error message
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
        setRemovingItemId(null);
        return;
      }
      
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to remove bank connection';
      setError(errorMessage);
      setRemovingItemId(null);
    }
  };

  const handleSyncBank = async (itemId: string) => {
    setSyncingItemId(itemId);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await syncAPI.syncTransactions(itemId);
      setSuccessMessage(
        `✅ Sync completed!\n` +
        `📊 Added: ${response.transactions_added}, Updated: ${response.transactions_updated}, Removed: ${response.transactions_removed}\n` +
        `💳 Accounts synced: ${response.accounts_synced}`
      );
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to sync transactions';
      setError(errorMessage);
    } finally {
      setSyncingItemId(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Manage Banks</h1>
          <p className="text-gray-600">
            View, add, and remove your connected bank accounts.
          </p>
        </div>

        {/* Error Message */}
        {error && <ErrorMessage message={error} />}

        {/* Success Message */}
        {successMessage && (
          <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg mb-6 whitespace-pre-line">
            {successMessage}
          </div>
        )}

        {/* Plaid Link Component */}
        {linkToken && (
          <PlaidLink
            linkToken={linkToken}
            onSuccess={handlePlaidSuccess}
            onExit={handlePlaidExit}
          />
        )}

        {/* Add Bank Button */}
        <div className="mb-6">
          <button
            onClick={handleCreateLinkToken}
            disabled={isCreatingLinkToken}
            className="w-full sm:w-auto px-6 py-3 min-h-[44px] bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isCreatingLinkToken ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Connecting...
              </>
            ) : (
              <>
                ➕ Add Another Bank
              </>
            )}
          </button>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {/* Empty State */}
        {!isLoading && plaidItems.length === 0 && (
          <div className="bg-white rounded-lg shadow-lg p-12 text-center">
            <div className="text-6xl mb-4">🏦</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">No Banks Connected</h2>
            <p className="text-gray-600 mb-6">
              Connect your first bank account to start tracking your cashback optimization.
            </p>
            <button
              onClick={handleCreateLinkToken}
              disabled={isCreatingLinkToken}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isCreatingLinkToken ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Connecting...
                </>
              ) : (
                <>
                  🔗 Connect Your First Bank
                </>
              )}
            </button>
          </div>
        )}

        {/* Banks List */}
        {!isLoading && plaidItems.length > 0 && (
          <div className="space-y-4">
            {plaidItems.map((item) => (
              <div key={item.id} className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <div className="text-3xl mr-3">🏦</div>
                      <div>
                        <h3 className="text-xl font-bold text-gray-900">
                          {item.institution_id || 'Unknown Bank'}
                        </h3>
                        <p className="text-sm text-gray-600">
                          Connected on {formatDate(item.created_at)}
                        </p>
                        {item.last_cursor && (
                          <p className="text-xs text-gray-500 mt-1">
                            Last synced: {formatDate(item.updated_at)}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
                    <button
                      onClick={() => handleSyncBank(item.id)}
                      disabled={syncingItemId === item.id || removingItemId === item.id}
                      className="w-full sm:w-auto px-4 py-2 min-h-[44px] bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                      {syncingItemId === item.id ? (
                        <>
                          <LoadingSpinner size="sm" className="mr-2" />
                          Syncing...
                        </>
                      ) : (
                        <>
                          🔄 Sync
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => handleRemoveBank(item.id)}
                      disabled={removingItemId === item.id || syncingItemId === item.id}
                      className="w-full sm:w-auto px-4 py-2 min-h-[44px] bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                      {removingItemId === item.id ? (
                        <>
                          <LoadingSpinner size="sm" className="mr-2" />
                          Removing...
                        </>
                      ) : (
                        <>
                          🗑️ Remove
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
