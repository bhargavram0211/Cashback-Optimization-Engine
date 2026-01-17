import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { CategoryBreakdown } from '../types';

interface CategoryChartProps {
  data: CategoryBreakdown[];
}

export const CategoryChart: React.FC<CategoryChartProps> = ({ data }) => {
  // Sort data by lost_savings descending
  const sortedData = [...data].sort((a, b) => b.lost_savings - a.lost_savings);

  // Format data for Recharts
  const chartData = sortedData.map((item) => ({
    category: item.category,
    lostSavings: item.lost_savings,
    actualCashback: item.actual_cashback,
    potentialCashback: item.potential_cashback,
  }));

  return (
    <div className="w-full h-96">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="category"
            angle={-45}
            textAnchor="end"
            height={100}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            label={{ value: 'Lost Savings ($)', angle: -90, position: 'insideLeft' }}
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            formatter={(value: number) => `$${value.toFixed(2)}`}
            labelStyle={{ color: '#374151', fontWeight: 'bold' }}
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '8px',
            }}
          />
          <Bar
            dataKey="lostSavings"
            fill="#ef4444"
            radius={[8, 8, 0, 0]}
            name="Lost Savings"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
