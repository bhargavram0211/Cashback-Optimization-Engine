import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { cardsAPI } from '../api/client';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import type { UnidentifiedCard, CardProduct } from '../types';

export const IdentifyCards: React.FC = () => {
  const { user } = useAuthStore();
  const [unidentifiedCards, setUnidentifiedCards] = useState<UnidentifiedCard[]>([]);
  const [cardProducts, setCardProducts] = useState<CardProduct[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [identifyingCardId, setIdentifyingCardId] = useState<string | null>(null);
  const [selectedProducts, setSelectedProducts] = useState<Record<string, string>>({});

  useEffect(() => {
    const fetchData = async () => {
      if (!user?.id) return;

      setIsLoading(true);
      setError(null);

      try {
        const [cards, products] = await Promise.all([
          cardsAPI.getUnidentifiedCards(user.id),
          cardsAPI.getCardProducts(),
        ]);
        setUnidentifiedCards(cards);
        setCardProducts(products);

        // Initialize selected products with first card product for each unidentified card
        const initialSelections: Record<string, string> = {};
        cards.forEach((card) => {
          if (products.length > 0) {
            initialSelections[card.id] = products[0].id;
          }
        });
        setSelectedProducts(initialSelections);
      } catch (err: any) {
        const errorMessage = err.response?.data?.detail || 'Failed to load cards';
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [user?.id]);

  const handleIdentify = async (userCardId: string) => {
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
      const errorMessage = err.response?.data?.detail || 'Failed to identify card';
      alert(errorMessage);
    } finally {
      setIdentifyingCardId(null);
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

  // Empty state - all cards identified
  if (unidentifiedCards.length === 0) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-lg shadow p-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">🔍 Identify Your Cards</h1>
            <p className="text-lg text-gray-700 mb-6">
              Link your bank accounts to specific card products so we can calculate accurate rewards.
            </p>

            <div className="bg-green-50 border border-green-200 text-green-800 px-6 py-4 rounded-lg mb-6">
              <p className="font-semibold text-lg mb-2">✅ All your cards are identified!</p>
              <p className="mb-4">
                All your Plaid-synced credit cards have been identified. You can now:
              </p>
              <ul className="list-disc list-inside space-y-1 ml-4">
                <li>View your <strong>Dashboard</strong> to see savings insights</li>
                <li>Explore the <strong>Card Discovery</strong> page to find new cards</li>
              </ul>
            </div>

            <div className="bg-blue-50 border border-blue-200 text-blue-800 px-6 py-4 rounded-lg">
              <p className="text-sm">
                💡 <strong>Tip:</strong> If you connect a new bank account, come back here to identify those cards.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">🔍 Identify Your Cards</h1>
          <p className="text-lg text-gray-700 mb-4">
            Link your bank accounts to specific card products so we can calculate accurate rewards.
          </p>
          <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg">
            📋 Found {unidentifiedCards.length} card{unidentifiedCards.length !== 1 ? 's' : ''} to identify
          </div>
        </div>

        <p className="text-gray-700 mb-6">
          We found these credit cards in your connected bank accounts. Please tell us which card product each one is:
        </p>

        {/* Unidentified Cards List */}
        <div className="space-y-6">
          {unidentifiedCards.map((card) => (
            <div key={card.id} className="bg-white rounded-lg shadow p-6">
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
                    onClick={() => handleIdentify(card.id)}
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

        {/* Footer note */}
        <div className="mt-8 text-center text-gray-600 text-sm">
          <p>Your card information is securely linked through Plaid</p>
        </div>
      </div>
    </div>
  );
};
