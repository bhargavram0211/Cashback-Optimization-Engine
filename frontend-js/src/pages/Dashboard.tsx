import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { reportsAPI, plaidAPI, itemsAPI, syncAPI, optimizeAPI, analyticsAPI } from '../api/client';
import { MetricCard } from '../components/MetricCard';
import { CategoryChart } from '../components/CategoryChart';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { SESSION_EXPIRED_MESSAGE } from '../constants/errors';
import type { SavingsReport, PlaidItemResponse, CardComparison, OptimizationOpportunity } from '../types';

export const Dashboard: React.FC = () => {
  const { user } = useAuthStore();
  const [report, setReport] = useState<SavingsReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnectingSandbox, setIsConnectingSandbox] = useState(false);
  const [sandboxMessage, setSandboxMessage] = useState<string | null>(null);
  
  // New state for optimize and sync
  const [plaidItems, setPlaidItems] = useState<PlaidItemResponse[]>([]);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [showSyncModal, setShowSyncModal] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [optimizeMessage, setOptimizeMessage] = useState<string | null>(null);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  
  // New state for enhanced dashboard features
  const [cardComparisons, setCardComparisons] = useState<CardComparison[]>([]);
  const [optimizationOpportunities, setOptimizationOpportunities] = useState<OptimizationOpportunity[]>([]);
  
  // Pagination state for Transaction Opportunities
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  useEffect(() => {
    const fetchReport = async () => {
      if (!user?.id) return;

      setIsLoading(true);
      setError(null);

      try {
        const data = await reportsAPI.getSavingsReport();
        setReport(data);
      } catch (err: any) {
        if (err.response?.status === 401) {
          setError(SESSION_EXPIRED_MESSAGE);
          setTimeout(() => {
            window.location.href = '/';
          }, 2000);
        } else if (err.response?.status === 404) {
          // No transactions found - this is expected for new users
          setReport(null);
        } else {
          const errorMessage = err.response?.data?.detail || 'Failed to load dashboard data';
          setError(errorMessage);
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchReport();
  }, [user?.id]);

  // Fetch PlaidItems when user is available
  useEffect(() => {
    const fetchPlaidItems = async () => {
      if (!user?.id) return;

      try {
        const items = await itemsAPI.getUserPlaidItems();
        setPlaidItems(items);
      } catch (err: any) {
        // Silently fail - user might not have any PlaidItems yet
        console.log('No PlaidItems found or error fetching:', err);
      }
    };

    fetchPlaidItems();
  }, [user?.id]);

  // Fetch card comparison and opportunities when report is loaded
  useEffect(() => {
    const fetchEnhancedData = async () => {
      if (!user?.id || !report) return;

      // Fetch card comparison
      try {
        const comparisons = await analyticsAPI.getCardComparison();
        setCardComparisons(comparisons);
      } catch (err: any) {
        console.log('Error fetching card comparison:', err);
      }

      // Fetch optimization opportunities
      try {
        const opportunities = await analyticsAPI.getOptimizationOpportunities();
        setOptimizationOpportunities(opportunities);
      } catch (err: any) {
        console.log('Error fetching optimization opportunities:', err);
      }
    };

    fetchEnhancedData();
  }, [user?.id, report]);

  const handleConnectSandbox = async () => {
    setIsConnectingSandbox(true);
    setSandboxMessage(null);
    setError(null);

    try {
      const response = await plaidAPI.connectSandbox();
      setSandboxMessage(
        `✅ ${response.message}\n` +
        `📊 Synced ${response.transactions_synced} transactions\n` +
        `💳 Found ${response.cards_found} credit card(s)`
      );
      
      // Refresh PlaidItems list
      if (user?.id) {
        const items = await itemsAPI.getUserPlaidItems();
        setPlaidItems(items);
      }
      
      // Wait a moment for the backend to process, then refresh the report
      setTimeout(async () => {
        try {
          if (user?.id) {
            const data = await reportsAPI.getSavingsReport();
            setReport(data);
          }
        } catch (err: any) {
          // If still no data, that's okay - user might need to identify cards first
          console.log('Report not yet available, may need to identify cards first');
        }
      }, 2000);
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError(SESSION_EXPIRED_MESSAGE);
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
      } else {
        const errorMessage = err.response?.data?.detail || 'Failed to connect to sandbox';
        setError(errorMessage);
      }
    } finally {
      setIsConnectingSandbox(false);
    }
  };

  const handleOptimize = async () => {
    setIsOptimizing(true);
    setOptimizeMessage(null);
    setError(null);

    try {
      const response = await optimizeAPI.optimizeAll();
      setOptimizeMessage(
        `✅ Optimization Complete!\n` +
        `📊 Processed ${response.total_transactions} transactions\n` +
        `✨ Optimized ${response.optimized} transactions\n` +
        `💰 Total Lost Savings: $${response.total_lost_savings.toFixed(2)}`
      );

      // Refresh dashboard after optimization
      setTimeout(async () => {
        if (user?.id) {
          try {
            const data = await reportsAPI.getSavingsReport();
            setReport(data);
          } catch (err: any) {
            console.log('Error refreshing report after optimization:', err);
          }
        }
      }, 1000);
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError(SESSION_EXPIRED_MESSAGE);
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
      } else {
        const errorMessage = err.response?.data?.detail || 'Failed to optimize transactions';
        setError(errorMessage);
      }
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleSync = async (itemId?: string) => {
    const targetItemId = itemId || selectedItemId;
    if (!targetItemId) {
      setError('Please select a bank account to sync');
      return;
    }

    setIsSyncing(true);
    setSyncMessage(null);
    setError(null);
    setShowSyncModal(false);

    try {
      const syncResponse = await syncAPI.syncTransactions(targetItemId);
      setSyncMessage(
        `✅ Sync Complete!\n` +
        `📊 Added ${syncResponse.transactions_added} transactions\n` +
        `🔄 Updated ${syncResponse.transactions_updated} transactions\n` +
        `💳 Synced ${syncResponse.accounts_synced} account(s)`
      );

      // Automatically run optimization after sync
      setTimeout(async () => {
        try {
          const optimizeResponse = await optimizeAPI.optimizeAll();
          setSyncMessage(
            (prev) => prev + 
            `\n\n✨ Auto-Optimized ${optimizeResponse.optimized} transactions\n` +
            `💰 Calculated $${optimizeResponse.total_lost_savings.toFixed(2)} in lost savings`
          );

          // Refresh dashboard after optimization
          setTimeout(async () => {
            if (user?.id) {
              try {
                const data = await reportsAPI.getSavingsReport();
                setReport(data);
              } catch (err: any) {
                console.log('Error refreshing report after sync and optimize:', err);
              }
            }
          }, 1000);
        } catch (optimizeErr: any) {
          console.log('Auto-optimize failed:', optimizeErr);
          // Still refresh dashboard even if optimize fails
          if (user?.id) {
            try {
              const data = await reportsAPI.getSavingsReport();
              setReport(data);
            } catch (err: any) {
              console.log('Error refreshing report:', err);
            }
          }
        }
      }, 1500);
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError(SESSION_EXPIRED_MESSAGE);
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
      } else {
        const errorMessage = err.response?.data?.detail || 'Failed to sync transactions';
        setError(errorMessage);
      }
    } finally {
      setIsSyncing(false);
    }
  };

  const handleSyncClick = () => {
    if (plaidItems.length === 0) {
      setError('No bank accounts connected. Please connect a bank account first.');
      return;
    }

    if (plaidItems.length === 1) {
      // Only one item, sync directly
      handleSync(plaidItems[0].id);
    } else {
      // Multiple items, show selection modal
      setShowSyncModal(true);
      setSelectedItemId(plaidItems[0].id); // Default to first item
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <ErrorMessage message={error} />
        </div>
      </div>
    );
  }

  if (!report) {
    // Empty state - no transactions
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-lg shadow p-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              💳 GetCardIQ Dashboard
            </h1>
            <p className="text-lg text-gray-700 mb-6">
              Maximize your credit card rewards by using the right card for every purchase.
            </p>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
              <h2 className="text-xl font-semibold text-blue-900 mb-2">👋 Welcome! Let's get you started.</h2>
              <p className="text-blue-800 mb-4">No transactions found yet.</p>
              <div className="text-blue-700">
                <p className="mb-2">To see your GetCardIQ insights:</p>
                <ol className="list-decimal list-inside space-y-1 ml-4">
                  <li>Connect your bank account (or use sandbox for testing)</li>
                  <li>Identify your credit cards</li>
                  <li>View your savings insights</li>
                </ol>
                <p className="mt-4 text-sm">
                  <strong>For testing:</strong> Use the "Connect Sandbox" button below to get test data.
                </p>
              </div>
            </div>

            {sandboxMessage && (
              <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg mb-4 whitespace-pre-line">
                {sandboxMessage}
              </div>
            )}

            <div className="flex gap-4">
              <button
                onClick={handleConnectSandbox}
                disabled={isConnectingSandbox}
                className="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg font-semibold hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {isConnectingSandbox ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Connecting Sandbox...
                  </>
                ) : (
                  <>
                    🧪 Connect Sandbox (Test Data)
                  </>
                )}
              </button>
              <button
                onClick={() => {
                  if (user?.id) {
                    setIsLoading(true);
                    reportsAPI.getSavingsReport()
                      .then(setReport)
                      .catch((err: any) => {
                        if (err.response?.status === 404) {
                          setReport(null);
                        } else {
                          setError(err.response?.data?.detail || 'Failed to load dashboard data');
                        }
                      })
                      .finally(() => setIsLoading(false));
                  }
                }}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold hover:shadow-lg transition-shadow"
              >
                🔄 Refresh Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const { summary, category_breakdown, top_recommendation } = report;

  // Calculate percentages
  const cashbackRate = summary.total_spent > 0
    ? (summary.total_earned / summary.total_spent) * 100
    : 0;
  
  const lostSavingsPercent = summary.total_spent > 0
    ? (summary.total_lost_savings / summary.total_spent) * 100
    : 0;

  return (
    <div className="px-3 md:px-6 py-4 md:py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-4 md:mb-6">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
            💳 GetCardIQ Dashboard
          </h1>
          <p className="text-lg text-gray-700 mb-4">
            Maximize your credit card rewards by using the right card for every purchase.
          </p>

          {/* Action Buttons */}
          {(plaidItems && plaidItems.length > 0) && (
            <div className="flex flex-wrap gap-4 mb-4">
              <button
                onClick={handleSyncClick}
                disabled={isSyncing || isOptimizing}
                className="w-full sm:w-auto px-6 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg font-semibold hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-h-[44px]"
              >
                {isSyncing ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Syncing...
                  </>
                ) : (
                  <>
                    🔄 Sync Transactions
                  </>
                )}
              </button>
              <button
                onClick={handleOptimize}
                disabled={isOptimizing || isSyncing}
                className="w-full sm:w-auto px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-h-[44px]"
              >
                {isOptimizing ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Optimizing...
                  </>
                ) : (
                  <>
                    ⚡ Optimize Transactions
                  </>
                )}
              </button>
            </div>
          )}

          {/* Success Messages */}
          {syncMessage && (
            <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg mb-4 whitespace-pre-line">
              {syncMessage}
            </div>
          )}
          {optimizeMessage && (
            <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg mb-4 whitespace-pre-line">
              {optimizeMessage}
            </div>
          )}
        </div>

        {/* Sync Item Selection Modal */}
        {showSyncModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Select Bank Account to Sync</h2>
              <p className="text-gray-600 mb-4">
                You have multiple bank accounts connected. Which one would you like to sync?
              </p>
              <div className="space-y-2 mb-6">
                {plaidItems.map((item) => (
                  <label
                    key={item.id}
                    className="flex items-center p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50"
                  >
                    <input
                      type="radio"
                      name="plaidItem"
                      value={item.id}
                      checked={selectedItemId === item.id}
                      onChange={(e) => setSelectedItemId(e.target.value)}
                      className="mr-3"
                    />
                    <div>
                      <p className="font-semibold text-gray-900">
                        {item.institution_id || 'Unknown Bank'}
                      </p>
                      <p className="text-sm text-gray-600">
                        Connected {new Date(item.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </label>
                ))}
              </div>
              <div className="flex gap-4">
                <button
                  onClick={() => handleSync()}
                  disabled={!selectedItemId || isSyncing}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg font-semibold hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSyncing ? 'Syncing...' : 'Sync Selected'}
                </button>
                <button
                  onClick={() => {
                    setShowSyncModal(false);
                    setSelectedItemId(null);
                  }}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Top-Level Metrics */}
        <div className="mb-8">
          <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-3 md:mb-4">📊 Your Spending Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <MetricCard
              label="💰 Total Spent"
              value={`$${summary.total_spent.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              help="Total amount spent across all transactions"
            />
            <MetricCard
              label="✨ Actual Rewards"
              value={`$${summary.total_earned.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              delta={`${cashbackRate.toFixed(2)}% cashback`}
              help="Total cashback earned with current card usage"
            />
            <MetricCard
              label="💸 Lost Savings"
              value={`$${summary.total_lost_savings.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              delta={`-${lostSavingsPercent.toFixed(2)}%`}
              deltaColor="inverse"
              help="Opportunity cost from not using optimal cards"
            />
          </div>
        </div>

        {/* Category Breakdown */}
        {category_breakdown && category_breakdown.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-3 md:mb-4">📈 Lost Savings by Category</h2>
            <div className="bg-white rounded-lg shadow p-4 md:p-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Chart */}
                <div className="lg:col-span-2">
                  <CategoryChart data={category_breakdown} />
                </div>

                {/* Key Insights */}
                <div className="lg:col-span-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">💡 Key Insights</h3>
                  {category_breakdown.length > 0 && (
                    <div className="space-y-4">
                      {category_breakdown
                        .sort((a, b) => b.lost_savings - a.lost_savings)
                        .slice(0, 2)
                        .map((cat, index) => (
                          <div key={cat.category} className="bg-gray-50 rounded-lg p-4">
                            <p className="font-semibold text-gray-900 mb-2">
                              {index === 0 ? 'Biggest Opportunity' : 'Second Opportunity'}: {cat.category}
                            </p>
                            <div className="text-sm text-gray-700 space-y-1">
                              <p>Lost: ${cat.lost_savings.toFixed(2)}</p>
                              <p>Spent: ${cat.total_spent.toFixed(2)}</p>
                              <p>Could earn: ${cat.potential_cashback.toFixed(2)}</p>
                            </div>
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Top Recommendation */}
        {top_recommendation && (
          <div className="mb-8">
            <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-3 md:mb-4">🏆 Top Card Recommendation</h2>
            <div className="bg-white rounded-lg shadow p-4 md:p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-2">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">
                    {top_recommendation.provider} {top_recommendation.card_name}
                  </h3>
                  <p className="text-gray-700 mb-4">
                    This card was the optimal choice for <strong>{top_recommendation.times_recommended}</strong> of your transactions.
                  </p>
                  <div className="space-y-2 text-gray-700">
                    <p>
                      <strong>Potential Savings:</strong> ${top_recommendation.total_potential_savings.toFixed(2)}
                    </p>
                    <p>
                      <strong>Avg per Transaction:</strong> ${top_recommendation.avg_savings_per_transaction.toFixed(2)}
                    </p>
                  </div>
                </div>
                <div className="md:col-span-1">
                  <div className="bg-purple-50 rounded-lg p-6 text-center">
                    <p className="text-sm text-gray-600 mb-2">Times Recommended</p>
                    <p className="text-4xl font-bold text-purple-600">
                      {top_recommendation.times_recommended}
                    </p>
                    <p className="text-xs text-gray-500 mt-2">
                      Number of transactions where this card was optimal
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Card Comparison Section */}
        {cardComparisons.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-3 md:mb-4">💳 Card Performance Comparison</h2>
            <div className="bg-white rounded-lg shadow p-4 md:p-6">
              <p className="text-gray-700 mb-4">
                Compare your cards by potential savings if used optimally for the transactions where they're the best choice.
              </p>
              {/* Desktop: Table */}
              <div className="hidden md:block overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Card
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Optimal Transactions
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Potential Savings
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {cardComparisons.map((card, index) => (
                      <tr key={`${card.provider}-${card.card_name}-${index}`} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {card.provider} {card.card_name}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-700">
                            {card.optimal_transaction_count}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-semibold text-green-600">
                            ${card.potential_savings.toFixed(2)}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile: Cards */}
              <div className="md:hidden space-y-3">
                {cardComparisons.map((card, index) => (
                  <div key={`${card.provider}-${card.card_name}-${index}`} className="bg-gray-50 rounded-lg p-4 border border-gray-200 space-y-2">
                    <div className="font-semibold text-gray-900">
                      {card.provider} {card.card_name}
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <div className="text-gray-500 text-xs">Optimal Transactions</div>
                        <div className="font-medium">{card.optimal_transaction_count}</div>
                      </div>
                      <div>
                        <div className="text-gray-500 text-xs">Potential Savings</div>
                        <div className="font-semibold text-green-600">
                          ${card.potential_savings.toFixed(2)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Optimization Opportunities Table */}
        {optimizationOpportunities.length > 0 && (() => {
          // Pagination logic
          const maxOpportunities = Math.min(optimizationOpportunities.length, 50);
          const totalPages = Math.ceil(maxOpportunities / itemsPerPage);
          const startIndex = (currentPage - 1) * itemsPerPage;
          const endIndex = startIndex + itemsPerPage;
          const paginatedOpportunities = optimizationOpportunities.slice(0, 50).slice(startIndex, endIndex);
          
          return (
            <div className="mb-8">
              <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-3 md:mb-4">🎯 Transaction Opportunities</h2>
              <div className="bg-white rounded-lg shadow p-4 md:p-6">
                <p className="text-gray-700 mb-4">
                  Top transactions where using a different card would have saved you money. Showing {maxOpportunities} opportunities.
                </p>
                {/* Desktop: Table View */}
                <div className="hidden md:block overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Merchant
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Category
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Amount
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Card Used
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Lost Savings
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Recommended Card
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {paginatedOpportunities.map((opp, index) => (
                        <tr key={`${opp.merchant_name}-${opp.date}-${index}`} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                            {opp.date ? new Date(opp.date).toLocaleDateString() : 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {opp.merchant_name || 'Unknown'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                            {opp.internal_bucket || 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                            ${Math.abs(opp.amount).toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                            {opp.used_card_provider && opp.used_card_name
                              ? `${opp.used_card_provider} ${opp.used_card_name}`
                              : 'Unknown'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-red-600">
                            ${opp.lost_savings.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                            {opp.best_card_provider && opp.best_card_name
                              ? `${opp.best_card_provider} ${opp.best_card_name}`
                              : 'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                
                {/* Mobile: Card View */}
                <div className="md:hidden space-y-3">
                  {paginatedOpportunities.map((opp, index) => (
                    <div 
                      key={`${opp.merchant_name}-${opp.date}-${index}`} 
                      className="bg-gray-50 rounded-lg p-4 border border-gray-200 space-y-3"
                    >
                      {/* Header: Merchant + Lost Savings */}
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="font-semibold text-gray-900 text-base">
                            {opp.merchant_name || 'Unknown'}
                          </div>
                          <div className="text-sm text-gray-600 mt-1">
                            {opp.date ? new Date(opp.date).toLocaleDateString() : 'N/A'}
                          </div>
                        </div>
                        <div className="text-right ml-4">
                          <div className="font-bold text-red-600 text-lg">
                            ${opp.lost_savings.toFixed(2)}
                          </div>
                          <div className="text-xs text-gray-500 uppercase">Lost</div>
                        </div>
                      </div>
                      
                      {/* Transaction Details */}
                      <div className="grid grid-cols-2 gap-2 text-sm pt-2 border-t border-gray-200">
                        <div>
                          <div className="text-gray-500 text-xs">Amount</div>
                          <div className="font-medium">${Math.abs(opp.amount).toFixed(2)}</div>
                        </div>
                        <div>
                          <div className="text-gray-500 text-xs">Category</div>
                          <div className="font-medium">{opp.internal_bucket || 'N/A'}</div>
                        </div>
                      </div>
                      
                      {/* Card Information */}
                      <div className="space-y-2 pt-2 border-t border-gray-200">
                        <div>
                          <div className="text-xs text-gray-500 mb-1">Card Used</div>
                          <div className="text-sm font-medium text-gray-700">
                            {opp.used_card_provider && opp.used_card_name 
                              ? `${opp.used_card_provider} ${opp.used_card_name}` 
                              : 'Unknown'}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-500 mb-1">Recommended Card</div>
                          <div className="text-sm font-semibold text-purple-600">
                            {opp.best_card_provider && opp.best_card_name 
                              ? `${opp.best_card_provider} ${opp.best_card_name}` 
                              : 'N/A'}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              
              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex flex-col sm:flex-row items-center justify-between mt-4 md:mt-6 gap-3 md:gap-4">
                  <div className="text-xs md:text-sm text-gray-700 text-center sm:text-left">
                    Showing {startIndex + 1} to {Math.min(endIndex, maxOpportunities)} of {maxOpportunities}
                  </div>
                  <div className="flex items-center gap-1 md:gap-2 flex-wrap justify-center">
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="px-3 md:px-4 py-2 min-h-[44px] border border-gray-300 rounded-lg text-xs md:text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Prev
                    </button>
                    
                    {/* Page numbers */}
                    <div className="flex gap-1">
                      {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                        <button
                          key={page}
                          onClick={() => setCurrentPage(page)}
                          className={`px-2 md:px-3 py-2 min-h-[44px] min-w-[44px] rounded-lg text-xs md:text-sm font-medium transition-colors ${
                            currentPage === page
                              ? 'bg-purple-600 text-white'
                              : 'text-gray-700 hover:bg-gray-100'
                          }`}
                        >
                          {page}
                        </button>
                      ))}
                    </div>
                    
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                      className="px-3 md:px-4 py-2 min-h-[44px] border border-gray-300 rounded-lg text-xs md:text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
          );
        })()}
      </div>
    </div>
  );
};
