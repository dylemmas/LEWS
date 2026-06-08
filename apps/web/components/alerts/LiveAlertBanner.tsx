'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { useAlertsStore } from '@/lib/stores/alerts';
import type { AlertEvent } from '@lews/shared-types';

export function LiveAlertBanner() {
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());
  const { topAlerts, prependAlert, clearAlert } = useAlertsStore();

  useEffect(() => {
    // In a real app, this would listen to Socket.IO events
    // For now, we'll poll as a placeholder
    const interval = setInterval(async () => {
      // Fetch latest open alerts
      const res = await fetch('/api/alerts?state=open&limit=1');
      if (res.ok) {
        const alerts = await res.json();
        if (alerts.length > 0) {
          const alert = alerts[0];
          if (!dismissed.has(alert.id)) {
            prependAlert(alert);
          }
        }
      }
    }, 15000);
    return () => clearInterval(interval);
  }, [dismissed, prependAlert]);

  const topAlert = topAlerts[0];
  if (!topAlert) return null;

  const handleDismiss = () => {
    setDismissed(prev => new Set(prev).add(topAlert.id));
    clearAlert(topAlert.id);
  };

  return (
    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-start gap-3">
      <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="text-red-400 font-semibold truncate">{topAlert.title}</div>
        <div className="text-zinc-400 text-sm truncate">{topAlert.message}</div>
      </div>
      <button
        onClick={handleDismiss}
        className="text-zinc-500 hover:text-zinc-300 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
