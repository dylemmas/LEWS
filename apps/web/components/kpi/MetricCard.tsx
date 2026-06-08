'use client';

import type { ReactNode } from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  critical?: number;
  warning?: number;
}

export function MetricCard({ title, value, subtitle, critical, warning }: MetricCardProps) {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
      <div className="text-zinc-400 text-sm mb-1">{title}</div>
      <div className="text-2xl font-semibold text-zinc-100">{value}</div>
      {subtitle && <div className="text-zinc-500 text-xs mt-1">{subtitle}</div>}
      {(critical !== undefined || warning !== undefined) && (
        <div className="flex gap-2 mt-2">
          {critical !== undefined && critical > 0 && (
            <span className="text-red-500 text-xs">🔴 {critical} critical</span>
          )}
          {warning !== undefined && warning > 0 && (
            <span className="text-orange-500 text-xs">🟠 {warning} warning</span>
          )}
        </div>
      )}
    </div>
  );
}
