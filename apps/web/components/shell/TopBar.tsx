'use client';

import { useEffect } from 'react';
import { AlertCircle, Wifi } from 'lucide-react';
import { useAlertsStore } from '@/lib/stores/alerts';
import { fixtures } from '@/lib/fixtures';

export function TopBar() {
  const { topAlerts, setAlerts } = useAlertsStore();

  useEffect(() => {
    setAlerts(
      fixtures.alerts
        .filter((a) => a.state === 'open')
        .slice(0, 5)
        .map((a) => ({
          alert_id: a.id,
          node_id: a.node_id,
          site_id: a.site_id,
          severity: a.severity,
          state: a.state,
          title: a.title,
          message: a.message,
          first_seen_at: a.first_seen_at,
          last_seen_at: a.last_seen_at,
          ml_prob: a.ml_prob,
        })),
    );
  }, [setAlerts]);

  const latestCritical = topAlerts.find((a) => a.severity === 3);

  if (latestCritical && latestCritical.state === 'open') {
    return (
      <header className="bg-red-900 border-b border-red-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AlertCircle className="text-red-400 animate-pulse" size={20} />
          <div>
            <span className="font-semibold text-white">CRITICAL ALERT:</span>
            <span className="text-red-200 ml-2">{latestCritical.title}</span>
          </div>
        </div>
        <div className="text-sm text-red-300">
          {new Date(latestCritical.last_seen_at).toLocaleTimeString()}
        </div>
      </header>
    );
  }

  return (
    <header className="bg-slate-900 border-b border-slate-800 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <span className="text-sm text-slate-400">
          <span className="text-slate-500">Tenant:</span> Acme Landslide Monitoring
        </span>
        <span className="text-sm text-slate-400">
          <Wifi size={14} className="inline mr-1 text-green-500" />
          System Online
        </span>
      </div>
    </header>
  );
}
