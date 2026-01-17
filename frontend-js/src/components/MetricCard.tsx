import React from 'react';

interface MetricCardProps {
  label: string;
  value: string;
  delta?: string;
  deltaColor?: 'normal' | 'inverse';
  help?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  delta,
  deltaColor = 'normal',
  help,
}) => {
  const deltaColorClass = deltaColor === 'inverse' 
    ? 'text-red-600' 
    : 'text-green-600';

  return (
    <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-medium text-gray-600">{label}</p>
        {help && (
          <div className="group relative">
            <svg
              className="w-4 h-4 text-gray-400 cursor-help"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z"
                clipRule="evenodd"
              />
            </svg>
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
              {help}
            </div>
          </div>
        )}
      </div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      {delta && (
        <p className={`text-sm font-medium mt-1 ${deltaColorClass}`}>
          {delta}
        </p>
      )}
    </div>
  );
};
