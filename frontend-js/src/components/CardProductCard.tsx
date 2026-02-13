import React, { useState } from 'react';
import type { CardProduct } from '../types';

interface CardProductCardProps {
  card: CardProduct;
}

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

const getBestCategoryForCard = (card: CardProduct): { bucket: string; multiplier: number } => {
  if (!card.reward_rules || card.reward_rules.length === 0) {
    return { bucket: 'All Purchases', multiplier: card.base_reward_rate };
  }
  
  const bestRule = card.reward_rules.reduce((best, current) =>
    current.multiplier > best.multiplier ? current : best
  );
  
  return { bucket: bestRule.bucket, multiplier: bestRule.multiplier };
};

export const CardProductCard: React.FC<CardProductCardProps> = ({ card }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const bestCategory = getBestCategoryForCard(card);

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6 hover:shadow-lg transition-shadow">
      {/* Card Image */}
      {card.image_url && (
        <div className="mb-4 flex justify-center">
          <img
            src={card.image_url}
            alt={`${card.provider} ${card.card_name}`}
            className="h-32 w-auto object-contain rounded-lg"
            onError={(e) => {
              // Hide image if it fails to load
              e.currentTarget.style.display = 'none';
            }}
          />
        </div>
      )}

      {/* Card Header */}
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-900 mb-1">{card.provider}</h3>
        <p className="text-lg font-semibold text-gray-700">{card.card_name}</p>
      </div>

      {/* Best Category Badge */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg text-center mb-4">
        <p className="font-semibold">
          Best: {bestCategory.multiplier}% {getCategoryIcon(bestCategory.bucket)} {bestCategory.bucket}
        </p>
      </div>

      {/* Base Rate */}
      <p className="text-sm text-gray-600 mb-4">
        Base: {card.base_reward_rate}% on all purchases
      </p>

      {/* Reward Rules */}
      {card.reward_rules && card.reward_rules.length > 0 && (
        <div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full text-left text-sm font-medium text-purple-600 hover:text-purple-700 flex items-center justify-between mb-2"
          >
            <span>{isExpanded ? 'Hide' : 'View'} Reward Details</span>
            <svg
              className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {isExpanded && (
            <div className="mt-2 space-y-1">
              {[...card.reward_rules]
                .sort((a, b) => b.multiplier - a.multiplier)
                .map((rule, index) => (
                  <div key={index} className="flex items-center text-sm text-gray-700">
                    <span className="mr-2">{getCategoryIcon(rule.bucket)}</span>
                    <span className="font-semibold">{rule.multiplier}%</span>
                    <span className="ml-2">{rule.bucket}</span>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}

      {/* Benefits Link */}
      {card.benefits_url && (
        <a
          href={card.benefits_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-block text-sm text-purple-600 hover:text-purple-700 font-medium"
        >
          View Benefits ↗
        </a>
      )}
    </div>
  );
};
