import React, { useEffect, useState, useMemo } from 'react';
import { cardsAPI } from '../api/client';
import { CardProductCard } from '../components/CardProductCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import type { CardProduct } from '../types';

const CATEGORIES = [
  'DINING',
  'GROCERY',
  'TRAVEL',
  'GAS',
  'DRUGSTORE',
  'ONLINE_SHOPPING',
  'ENTERTAINMENT',
] as const;

const getCategoryIcon = (bucket: string): string => {
  const icons: Record<string, string> = {
    DINING: '🍽️',
    GROCERY: '🛒',
    TRAVEL: '✈️',
    GAS: '⛽',
    DRUGSTORE: '💊',
    ONLINE_SHOPPING: '🛍️',
    ENTERTAINMENT: '🎬',
    GENERAL: '💳',
  };
  return icons[bucket] || '💳';
};

type SortOption = 'provider' | 'base_rate' | 'num_categories';

export const CardDiscovery: React.FC = () => {
  const [cards, setCards] = useState<CardProduct[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<SortOption>('provider');

  useEffect(() => {
    const fetchCards = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const data = await cardsAPI.getCardProducts();
        setCards(data);
      } catch (err: any) {
        const errorMessage = err.response?.data?.detail || 'Failed to load cards';
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCards();
  }, []);

  // Filter and sort cards
  const filteredAndSortedCards = useMemo(() => {
    let filtered = [...cards];

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (card) =>
          card.provider.toLowerCase().includes(query) ||
          card.card_name.toLowerCase().includes(query)
      );
    }

    // Apply category filter
    if (categoryFilter.length > 0) {
      filtered = filtered.filter((card) =>
        card.reward_rules.some((rule) => categoryFilter.includes(rule.bucket))
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'provider':
          const providerCompare = a.provider.localeCompare(b.provider);
          if (providerCompare !== 0) return providerCompare;
          return a.card_name.localeCompare(b.card_name);
        case 'base_rate':
          return b.base_reward_rate - a.base_reward_rate;
        case 'num_categories':
          return b.reward_rules.length - a.reward_rules.length;
        default:
          return 0;
      }
    });

    return filtered;
  }, [cards, searchQuery, categoryFilter, sortBy]);

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

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">🔍 Card Discovery</h1>
          <p className="text-lg text-gray-700">
            Explore credit cards and find the best ones for your spending.
          </p>
        </div>

        {/* Success message */}
        {cards.length > 0 && (
          <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg mb-6">
            ✅ Found {cards.length} credit cards
          </div>
        )}

        {/* Search and Filters */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div className="md:col-span-2">
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
                🔍 Search by provider or card name
              </label>
              <input
                id="search"
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search cards..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
              />
            </div>

            {/* Category Filter */}
            <div>
              <label htmlFor="category-filter" className="block text-sm font-medium text-gray-700 mb-2">
                Filter by category
              </label>
              <select
                id="category-filter"
                multiple
                value={categoryFilter}
                onChange={(e) => {
                  const selected = Array.from(e.target.selectedOptions, (option) => option.value);
                  setCategoryFilter(selected);
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                size={3}
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {getCategoryIcon(cat)} {cat}
                  </option>
                ))}
              </select>
              {categoryFilter.length > 0 && (
                <button
                  onClick={() => setCategoryFilter([])}
                  className="mt-2 text-sm text-purple-600 hover:text-purple-700"
                >
                  Clear filters
                </button>
              )}
            </div>

            {/* Sort */}
            <div>
              <label htmlFor="sort" className="block text-sm font-medium text-gray-700 mb-2">
                Sort by
              </label>
              <select
                id="sort"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortOption)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
              >
                <option value="provider">Provider (A-Z)</option>
                <option value="base_rate">Highest Base Rate</option>
                <option value="num_categories">Most Categories</option>
              </select>
            </div>
          </div>
        </div>

        {/* Results count */}
        <div className="mb-4">
          <p className="text-gray-700">
            <strong>Showing {filteredAndSortedCards.length} cards</strong>
          </p>
        </div>

        {/* Card Grid */}
        {filteredAndSortedCards.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-600">No cards match your search criteria.</p>
            <button
              onClick={() => {
                setSearchQuery('');
                setCategoryFilter([]);
              }}
              className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              Clear Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAndSortedCards.map((card) => (
              <CardProductCard key={card.id} card={card} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
