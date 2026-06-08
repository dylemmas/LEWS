'use client';

import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface SparklineProps {
  data: number[];
  height?: number;
  color?: string;
}

export function Sparkline({ data, height = 60, color = '#3b82f6' }: SparklineProps) {
  const formatted = data.map((v, i) => ({ i, v }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={formatted} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
        <XAxis dataKey="i" hide />
        <YAxis hide domain={[0, 3]} />
        <Tooltip
          contentStyle={{ backgroundColor: '#18181b', border: 'none', borderRadius: 8 }}
          labelStyle={{ color: '#a1a1aa' }}
          formatter={(v: number) => [v.toFixed(2), 'severity']}
        />
        <Area type="monotone" dataKey="v" stroke={color} fill={color} fillOpacity={0.3} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
