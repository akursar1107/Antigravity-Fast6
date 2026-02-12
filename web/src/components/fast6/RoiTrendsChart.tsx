"use client";

import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { RoiTrend } from '@/lib/api';

interface RoiTrendsChartProps {
  data: RoiTrend[];
}

export default function RoiTrendsChart({ data }: RoiTrendsChartProps) {
  // Transform API data to match the chart's expected format if needed, 
  // or just use the data directly if it matches.
  // The API returns RoiTrend[] which has { week, roi_dollars, ... }
  // The original component expected a different structure with keys for each user.
  // Since we only have the current user's trend or aggregate data, we might need to adjust.
  // For now, let's assume we are plotting the current user's ROI trends.
  // If the API returns a signle user's trend, we can plot that.
  
  // However, the original chart plotted multiple users. 
  // The API `getRoiTrends` returns `RoiTrend[]` which seems to be for a single view or aggregate?
  // Let's look at `RoiTrend` type again: { week: number, picks_count: number, correct_count: number, accuracy: number, roi_dollars: number }
  // This looks like it's for the currently logged-in user or a specific context.
  // The original chart compared multiple users.
  // To keep it simple for this "Dashboard" view which seems personalized, we will plot the data we have.
  // If we want to compare, we'd need a different API endpoint or multiple calls.
  
  // We will map the data to a format Recharts understands for a single line for now, 
  // or mock the "friends" data if we want to preserve the look.
  // Let's just plot the main user for now to be accurate to the data we have.

  return (
    <div className="w-full h-[250px] mt-4 font-mono">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          {/* Grid: Salty Dog Tint */}
          <CartesianGrid strokeDasharray="2 2" stroke="#234058" vertical={true} opacity={0.15} />
          
          <XAxis 
            dataKey="week" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: '#234058', fontSize: 10, fontWeight: 'bold', fontFamily: 'monospace', opacity: 0.8 }} 
            dy={10}
            tickFormatter={(value) => `W${value}`}
          />
          <YAxis hide={true} domain={['auto', 'auto']} />
          
          <Tooltip 
            contentStyle={{ backgroundColor: '#F1EEE6', border: '2px solid #234058', borderRadius: '0px', color: '#234058' }}
            itemStyle={{ fontSize: '12px', fontFamily: 'monospace', color: '#234058', fontWeight: 'bold' }}
            labelStyle={{ color: '#A2877D', marginBottom: '5px' }}
            cursor={{ stroke: '#234058', strokeWidth: 1, strokeDasharray: '4 4' }}
            labelFormatter={(value) => `Week ${value}`}
          />

          <ReferenceLine y={0} stroke="#94a3b8" strokeWidth={2} />

          {/* YOU (Deep Tanager - #8C302C) */}
          <Line 
            type="step" 
            dataKey="roi_dollars" 
            stroke="#8C302C" 
            strokeWidth={3} 
            dot={{ r: 3, fill: '#8C302C' }} 
            activeDot={{ r: 6, stroke: '#F1EEE6', strokeWidth: 2 }} 
            name="ROI $"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
