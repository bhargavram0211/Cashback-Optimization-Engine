import React, { useEffect, useState, useMemo, useRef } from 'react';
import { cardsAPI } from '../api/client';
import { CardProductCard } from '../components/CardProductCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { SESSION_EXPIRED_MESSAGE } from '../constants/errors';
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

type SortOption = 'provider' | 'base_rate' | 'num_categories';

export const CardDiscovery: React.FC = () => {
  const [cards, setCards] = useState<CardProduct[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<SortOption>('provider');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchCards = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const data = await cardsAPI.getCardProducts();
        setCards(data);
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
        setIsLoading(false);
      }
    };

    fetchCards();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleCategory = (category: string) => {
    setCategoryFilter(prev =>
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const clearFilters = () => {
    setCategoryFilter([]);
  };

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
    <div className="px-3 md:px-6 py-4 md:py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-4 md:mb-6">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">🔍 Card Discovery</h1>
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
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Search */}
            <div className="lg:col-span-2">
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

            {/* Category Filter - Custom Dropdown */}
            <div className="relative" ref={dropdownRef}>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by category
              </label>
              
              {/* Selected Categories Display */}
              <button
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent bg-white text-left flex items-center justify-between"
              >
                <span className="text-sm text-gray-700">
                  {categoryFilter.length === 0
                    ? 'Select categories...'
                    : `${categoryFilter.length} selected`}
                </span>
                <span className="text-gray-500">{isDropdownOpen ? '▲' : '▼'}</span>
              </button>

              {/* Selected Chips */}
              {categoryFilter.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {categoryFilter.map((cat) => (
                    <span
                      key={cat}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-purple-100 text-purple-800"
                    >
                      {cat.replace(/_/g, ' ')}
                      <button
                        onClick={() => toggleCategory(cat)}
                        className="ml-2 text-purple-600 hover:text-purple-800"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}

              {/* Dropdown Menu */}
              {isDropdownOpen && (
                <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg max-h-64 overflow-y-auto">
                  <div className="p-2">
                    {CATEGORIES.map((cat) => (
                      <label
                        key={cat}
                        className="flex items-center px-3 py-2 hover:bg-gray-50 rounded cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={categoryFilter.includes(cat)}
                          onChange={() => toggleCategory(cat)}
                          className="mr-3 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                        />
                        <span className="text-sm text-gray-700">{cat.replace(/_/g, ' ')}</span>
                      </label>
                    ))}
                  </div>
                  {categoryFilter.length > 0 && (
                    <div className="border-t border-gray-200 p-2">
                      <button
                        onClick={clearFilters}
                        className="w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded"
                      >
                        Clear All
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

          </div>

          {/* Sort - Separate row */}
          <div className="mt-4">
            <label htmlFor="sort" className="block text-sm font-medium text-gray-700 mb-2">
              Sort by
            </label>
            <select
              id="sort"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="w-full md:w-64 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
            >
              <option value="provider">Provider (A-Z)</option>
              <option value="base_rate">Highest Base Rate</option>
              <option value="num_categories">Most Categories</option>
            </select>
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
              className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 min-h-[44px]"
            >
              Clear Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAndSortedCards.map((card) => (
              <CardProductCard key={card.id} card={card} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
