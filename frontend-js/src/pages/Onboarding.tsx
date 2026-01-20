import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { plaidAPI, cardsAPI, authAPI, itemsAPI } from '../api/client';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { PlaidLink, getPlaidExitErrorMessage } from '../components/PlaidLink';
import { SESSION_EXPIRED_MESSAGE } from '../constants/errors';
import type { UnidentifiedCard, CardProduct, PlaidLinkOnSuccessMetadata, PlaidLinkOnExitMetadata } from '../types';

export const Onboarding: React.FC = () => {
  const navigate = useNavigate();
  const { user, setUser } = useAuthStore();
  const [currentStep, setCurrentStep] = useState(1);
  const [sandboxConnected, setSandboxConnected] = useState(false);
  const [sandboxMessage, setSandboxMessage] = useState<string | null>(null);
  const [isConnectingSandbox, setIsConnectingSandbox] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Plaid Link state
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [isCreatingLinkToken, setIsCreatingLinkToken] = useState(false);
  const [plaidConnected, setPlaidConnected] = useState(false);
  const [plaidMessage, setPlaidMessage] = useState<string | null>(null);
  const [cardsFound, setCardsFound] = useState(0);

  // Step 3 state (Identify Cards)
  const [unidentifiedCards, setUnidentifiedCards] = useState<UnidentifiedCard[]>([]);
  const [cardProducts, setCardProducts] = useState<CardProduct[]>([]);
  const [isLoadingCards, setIsLoadingCards] = useState(false);
  const [identifyingCardId, setIdentifyingCardId] = useState<string | null>(null);
  const [selectedProducts, setSelectedProducts] = useState<Record<string, string>>({});
  const [isCompletingOnboarding, setIsCompletingOnboarding] = useState(false);
  const [hadCardsToIdentify, setHadCardsToIdentify] = useState(false);

  // Calculate progress percentage
  const progress = ((currentStep - 1) / 3) * 100;

  // Fetch cards when on Step 3
  useEffect(() => {
    const fetchCards = async () => {
      if (currentStep === 3 && user?.id) {
        setIsLoadingCards(true);
        setError(null);

        try {
          const [cards, products] = await Promise.all([
            cardsAPI.getUnidentifiedCards(user.id),
            cardsAPI.getCardProducts(),
          ]);
          setUnidentifiedCards(cards);
          setCardProducts(products);
          setHadCardsToIdentify(cards.length > 0);

          // Initialize selected products
          const initialSelections: Record<string, string> = {};
          cards.forEach((card) => {
            if (products.length > 0) {
              initialSelections[card.id] = products[0].id;
            }
          });
          setSelectedProducts(initialSelections);
        } catch (err: any) {
          if (err.response?.status === 401) {
            setError(SESSION_EXPIRED_MESSAGE);
            setTimeout(() => {
              window.location.href = '/';
            }, 2000);
          } else {
            const errorMessage = err.response?.data?.detail || 'Failed to load cards';
            setError(errorMessage);
          }
        } finally {
          setIsLoadingCards(false);
        }
      }
    };

    fetchCards();
  }, [currentStep, user?.id]);

  // Auto-complete onboarding when all cards are identified (or no cards found)
  useEffect(() => {
    if (
      currentStep === 3 &&
      unidentifiedCards.length === 0 &&
      !isLoadingCards &&
      !isCompletingOnboarding &&
      (plaidConnected || sandboxConnected)
    ) {
      // Auto-complete if:
      // 1. There were cards and all are identified, OR
      // 2. No cards were found at all (user can still proceed)
      // All cards identified, auto-complete onboarding
      const autoComplete = async () => {
        setIsCompletingOnboarding(true);
        setError(null);

        try {
          await authAPI.markOnboardingComplete();
          
          // Update user state in store
          if (user) {
            setUser({
              ...user,
              onboarding_completed: true,
            });
          }

          // Show success message briefly, then redirect
          setTimeout(() => {
            navigate('/dashboard');
          }, 2000);
        } catch (err: any) {
          if (err.response?.status === 401) {
            setError(SESSION_EXPIRED_MESSAGE);
            setTimeout(() => {
              window.location.href = '/';
            }, 2000);
          } else {
            const errorMessage = err.response?.data?.detail || 'Failed to complete onboarding';
            setError(errorMessage);
          }
          setIsCompletingOnboarding(false);
        }
      };

      // Small delay to ensure UI has updated
      const timer = setTimeout(() => {
        autoComplete();
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [currentStep, unidentifiedCards.length, isLoadingCards, cardProducts.length, isCompletingOnboarding, plaidConnected, sandboxConnected, hadCardsToIdentify, user, setUser, navigate]);

  const handleConnectSandbox = async () => {
    setIsConnectingSandbox(true);
    setSandboxMessage(null);
    setError(null);

    try {
      const response = await plaidAPI.connectSandbox();
      setSandboxConnected(true);
      setCardsFound(response.cards_found);
      setSandboxMessage(
        `✅ ${response.message}\n` +
        `📊 Synced ${response.transactions_synced} transactions\n` +
        `💳 Found ${response.cards_found} credit card(s)`
      );

      // Refresh PlaidItems list
      if (user?.id) {
        await itemsAPI.getUserPlaidItems(user.id);
      }
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

  const handleCreateLinkToken = async () => {
    setIsCreatingLinkToken(true);
    setError(null);

    try {
      const response = await plaidAPI.createLinkToken();
      setLinkToken(response.link_token);
    } catch (err: any) {
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
    setIsCreatingLinkToken(false);

    try {
      const response = await plaidAPI.exchangeToken({
        public_token: publicToken,
        institution_id: metadata.institution.institution_id,
        institution_name: metadata.institution.name,
      });

      setPlaidConnected(true);
      setCardsFound(response.cards_found);
      setPlaidMessage(
        `✅ Successfully connected to ${response.institution_name}\n` +
        `📊 Synced ${response.transactions_synced} transactions\n` +
        `💳 Found ${response.cards_found} credit card(s)`
      );

      // Refresh PlaidItems list
      if (user?.id) {
        await itemsAPI.getUserPlaidItems(user.id);
      }

      // Reset link token so Link doesn't auto-open again
      setLinkToken(null);
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError(SESSION_EXPIRED_MESSAGE);
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
      } else {
        const errorMessage = err.response?.data?.detail || 'Failed to exchange token';
        setError(errorMessage);
      }
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

  const handleIdentifyCard = async (userCardId: string) => {
    const cardProductId = selectedProducts[userCardId];
    if (!cardProductId) {
      return;
    }

    setIdentifyingCardId(userCardId);
    try {
      await cardsAPI.identifyCard(userCardId, cardProductId);
      // Remove the identified card from the list
      setUnidentifiedCards((prev) => prev.filter((card) => card.id !== userCardId));
      // Remove from selected products
      const newSelections = { ...selectedProducts };
      delete newSelections[userCardId];
      setSelectedProducts(newSelections);
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError(SESSION_EXPIRED_MESSAGE);
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
      } else {
        const errorMessage = err.response?.data?.detail || 'Failed to identify card';
        alert(errorMessage);
      }
    } finally {
      setIdentifyingCardId(null);
    }
  };

  const handleCompleteOnboarding = async () => {
    setIsCompletingOnboarding(true);
    setError(null);

    try {
      const response = await authAPI.markOnboardingComplete();
      
      // Update user state in store
      if (user) {
        setUser({
          ...user,
          onboarding_completed: true,
        });
      }

      // Redirect to dashboard after a brief delay
      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError(SESSION_EXPIRED_MESSAGE);
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
      } else {
        const errorMessage = err.response?.data?.detail || 'Failed to complete onboarding';
        setError(errorMessage);
      }
      setIsCompletingOnboarding(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">
              Step {currentStep} of 3
            </span>
            <span className="text-sm font-medium text-gray-700">
              {Math.round(progress)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-gradient-to-r from-purple-600 to-blue-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Error Message */}
        {error && <ErrorMessage message={error} />}

        {/* Step 1: Welcome */}
        {currentStep === 1 && (
          <div className="bg-white rounded-lg shadow-xl p-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-4 text-center">
              🚀 Welcome to Cashback Optimizer!
            </h1>
            <p className="text-center text-gray-600 mb-8 text-lg">
              Maximize your credit card rewards by using the right card for every purchase.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div className="bg-purple-50 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-3">📊 Real-Time Analysis</h3>
                <p className="text-gray-700 mb-2">We analyze every transaction to show you:</p>
                <ul className="list-disc list-inside space-y-1 text-gray-600">
                  <li>How much cashback you earned</li>
                  <li>How much you could have earned</li>
                  <li>Which card would have been better</li>
                </ul>
              </div>

              <div className="bg-blue-50 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-3">🎯 Smart Recommendations</h3>
                <p className="text-gray-700 mb-2">Get personalized suggestions for:</p>
                <ul className="list-disc list-inside space-y-1 text-gray-600">
                  <li>Optimal card usage</li>
                  <li>New cards to apply for</li>
                  <li>Categories where you're losing money</li>
                </ul>
              </div>

              <div className="bg-green-50 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-3">🔒 Secure & Private</h3>
                <p className="text-gray-700 mb-2">Your data is protected:</p>
                <ul className="list-disc list-inside space-y-1 text-gray-600">
                  <li>Bank connections via Plaid (bank-level security)</li>
                  <li>We never store your login credentials</li>
                  <li>Your data is encrypted and private</li>
                </ul>
              </div>

              <div className="bg-yellow-50 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-3">💡 Easy to Use</h3>
                <p className="text-gray-700 mb-2">Get started in minutes:</p>
                <ul className="list-disc list-inside space-y-1 text-gray-600">
                  <li>Connect in under 2 minutes</li>
                  <li>Automatic transaction syncing</li>
                  <li>Beautiful, intuitive dashboard</li>
                </ul>
              </div>
            </div>

            <div className="flex justify-center">
              <button
                onClick={() => setCurrentStep(2)}
                className="px-8 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold hover:shadow-lg transition-shadow text-lg"
              >
                Get Started →
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Connect Bank */}
        {currentStep === 2 && (
          <div className="bg-white rounded-lg shadow-xl p-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Connect Your Bank</h2>
            <p className="text-gray-700 mb-6">
              We use <strong>Plaid</strong> to securely connect to your bank. Plaid is trusted by:
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-700 mb-6 ml-4">
              <li>Venmo, Cash App, and thousands of fintech apps</li>
              <li>Used by over 12,000+ financial institutions</li>
              <li>Bank-level 256-bit encryption</li>
            </ul>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <p className="text-blue-800">
                💡 <strong>Tip:</strong> You can connect multiple banks if you have credit cards from different institutions.
              </p>
            </div>

            {/* Plaid Link Component */}
            {linkToken && (
              <PlaidLink
                linkToken={linkToken}
                onSuccess={handlePlaidSuccess}
                onExit={handlePlaidExit}
              />
            )}

            {/* Connection Status */}
            {(plaidConnected || sandboxConnected) && (
              <div className="mb-6">
                {plaidMessage && (
                  <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg mb-4 whitespace-pre-line">
                    {plaidMessage}
                  </div>
                )}
                {sandboxMessage && (
                  <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg mb-4 whitespace-pre-line">
                    {sandboxMessage}
                  </div>
                )}
                {(plaidConnected || sandboxConnected) && cardsFound === 0 && (
                  <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg mb-4">
                    ⚠️ No credit cards found. You can still proceed to the dashboard.
                  </div>
                )}
              </div>
            )}

            {/* Connection Buttons */}
            {!plaidConnected && !sandboxConnected && (
              <div className="mb-6 space-y-4">
                <button
                  onClick={handleCreateLinkToken}
                  disabled={isCreatingLinkToken || isConnectingSandbox}
                  className="w-full px-6 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {isCreatingLinkToken ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Connecting...
                    </>
                  ) : (
                    <>
                      🔗 Connect Bank with Plaid Link
                    </>
                  )}
                </button>

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-300"></div>
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-white text-gray-500">Or</span>
                  </div>
                </div>

                <button
                  onClick={handleConnectSandbox}
                  disabled={isConnectingSandbox || isCreatingLinkToken}
                  className="w-full px-6 py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg font-semibold hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
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
              </div>
            )}

            <div className="flex gap-4">
              <button
                onClick={() => setCurrentStep(1)}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
              >
                ← Back
              </button>
              <button
                onClick={() => setCurrentStep(3)}
                disabled={!plaidConnected && !sandboxConnected}
                className="flex-1 px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Continue →
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Identify Cards */}
        {currentStep === 3 && (
          <div className="bg-white rounded-lg shadow-xl p-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Identify Your Cards</h2>
            <p className="text-gray-700 mb-6">
              Great! We found your credit card accounts. Please tell us which card product each account represents.
            </p>

            {isLoadingCards ? (
              <div className="flex items-center justify-center py-12">
                <LoadingSpinner size="lg" />
              </div>
            ) : unidentifiedCards.length === 0 && !isLoadingCards ? (
              <div>
                {hadCardsToIdentify ? (
                  <div className="bg-green-50 border border-green-200 text-green-800 px-6 py-4 rounded-lg mb-6">
                    <p className="font-semibold text-lg mb-2">✅ All cards identified!</p>
                    <p className="mb-4">
                      All your Plaid-synced credit cards have been identified. You're ready to start optimizing!
                    </p>
                  </div>
                ) : (
                  <div className="bg-blue-50 border border-blue-200 text-blue-800 px-6 py-4 rounded-lg mb-6">
                    <p className="font-semibold text-lg mb-2">ℹ️ No cards to identify</p>
                    <p className="mb-4">
                      We didn't find any credit cards in your connected bank account. You can still proceed to the dashboard.
                    </p>
                  </div>
                )}

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">🎉 You're All Set!</h3>
                  <p className="text-gray-700 mb-4">
                    Your account is configured and ready to go. You can now:
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-gray-700 ml-4">
                    <li>View your cashback optimization dashboard</li>
                    <li>See where you're losing money</li>
                    <li>Discover better card options</li>
                  </ul>
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={() => setCurrentStep(2)}
                    className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
                  >
                    ← Back
                  </button>
                  <button
                    onClick={handleCompleteOnboarding}
                    disabled={isCompletingOnboarding}
                    className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                  >
                    {isCompletingOnboarding ? (
                      <>
                        <LoadingSpinner size="sm" className="mr-2" />
                        Completing...
                      </>
                    ) : (
                      <>
                        Go to Dashboard →
                      </>
                    )}
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg mb-6">
                  📋 Found {unidentifiedCards.length} card{unidentifiedCards.length !== 1 ? 's' : ''} to identify
                </div>

                <div className="space-y-6 mb-6">
                  {unidentifiedCards.map((card) => (
                    <div key={card.id} className="bg-gray-50 rounded-lg p-6">
                      <div className="mb-4">
                        <h3 className="text-xl font-bold text-gray-900 mb-1">🃏 {card.official_name}</h3>
                        <p className="text-sm text-gray-600">
                          Account ending in <strong>{card.mask}</strong>
                        </p>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                        <div className="md:col-span-3">
                          <label htmlFor={`select-${card.id}`} className="block text-sm font-medium text-gray-700 mb-2">
                            Which card is this?
                          </label>
                          <select
                            id={`select-${card.id}`}
                            value={selectedProducts[card.id] || ''}
                            onChange={(e) =>
                              setSelectedProducts({ ...selectedProducts, [card.id]: e.target.value })
                            }
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                          >
                            {cardProducts.map((product) => (
                              <option key={product.id} value={product.id}>
                                {product.provider} {product.card_name}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div className="md:col-span-1">
                          <button
                            onClick={() => handleIdentifyCard(card.id)}
                            disabled={identifyingCardId === card.id || !selectedProducts[card.id]}
                            className="w-full px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                          >
                            {identifyingCardId === card.id ? (
                              <>
                                <LoadingSpinner size="sm" className="mr-2" />
                                Identifying...
                              </>
                            ) : (
                              '✅ Identify'
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={() => setCurrentStep(2)}
                    className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
                  >
                    ← Back
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
