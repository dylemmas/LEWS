'use client';

import type { AlertDTO, AlertState, Severity } from '@lews/shared-types';

interface AlertListProps {
  alerts: AlertDTO[];
  onAck: (id: string) => void;
  onResolve: (id: string) => void;
}

const SEVERITY_COLORS: Record<Severity, { bg: string; text: string; border: string }> = {
  0: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20' },
  1: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/20' },
  2: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20' },
  3: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20' },
};

const SEVERITY_LABELS: Record<Severity, string> = {
  0: 'Normal',
  1: 'Watch',
  2: 'Warning',
  3: 'Critical',
};

export default function AlertList({ alerts, onAck, onResolve }: AlertListProps) {
  if (alerts.length === 0) {
    return (
      <div className="rounded border border-slate-800 bg-slate-900 p-8">
        <div className="text-center text-slate-500">No active alerts</div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <AlertCard key={alert.id} alert={alert} onAck={onAck} onResolve={onResolve} />
      ))}
    </div>
  );
}

function AlertCard({ alert, onAck, onResolve }: { alert: AlertDTO; onAck: (id: string) => void; onResolve: (id: string) => void }) {
  const severityColors = SEVERITY_COLORS[alert.severity as Severity];
  const isOpen = alert.state === 'open';
  const isAcked = alert.state === 'acknowledged';

  return (
    <div
      className={`rounded border ${severityColors.border} ${severityColors.bg} p-4`}
    >
      <div className="mb-2 flex items-start justify-between">
        <div className="flex-1">
          <div className="mb-1 flex items-center gap-2">
            <span
              className={`rounded border px-2 py-0.5 text-xs font-medium ${severityColors.border} ${severityColors.text}`}
            >
              {SEVERITY_LABELS[alert.severity as Severity]}
            </span>
            <span className="text-xs text-slate-500 capitalize">{alert.state}</span>
          </div>
          <h3 className="font-semibold text-white">{alert.title}</h3>
          <p className="mt-1 text-sm text-slate-400">{alert.message}</p>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between border-t border-slate-800 pt-3">
        <div className="text-xs text-slate-500">
          First seen: {new Date(alert.first_seen_at).toLocaleString()}
        </div>
        <div className="flex gap-2">
          {isOpen && (
            <button
              onClick={() => onAck(alert.id)}
              className="rounded bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-sky-700"
            >
              Acknowledge
            </button>
          )}
          {(isOpen || isAcked) && (
            <button
              onClick={() => onResolve(alert.id)}
              className="rounded bg-green-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-green-700"
            >
              Resolve
            </button>
          )}
          <a
            href={`/nodes/${alert.node_id}`}
            className="rounded border border-slate-700 px-3 py-1.5 text-sm font-medium text-slate-400 transition hover:border-slate-600 hover:text-white"
          >
            View Node
          </a>
        </div>
      </div>
    </div>
  );
}
