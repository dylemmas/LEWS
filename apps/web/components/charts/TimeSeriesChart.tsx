'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { format } from 'date-fns';

interface TimeSeriesChartProps {
  data: Array<{ time: string; [key: string]: string | number }>;
  lines: Array<{ key: string; label: string; color: string }>;
  height?: number;
}

export function TimeSeriesChart({ data, lines, height = 300 }: TimeSeriesChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
        <XAxis
          dataKey="time"
          tickFormatter={(v) => format(new Date(v), 'HH:mm')}
          stroke="#888"
        />
        <YAxis stroke="#888" />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1a1a1a',
            border: '1px solid #333',
            borderRadius: '4px',
          }}
          labelFormatter={(v) => format(new Date(v), 'yyyy-MM-dd HH:mm:ss')}
        />
        <Legend />
        {lines.map((line) => (
          <Line
            key={line.key}
            type="monotone"
            dataKey={line.key}
            name={line.label}
            stroke={line.color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
