'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  AlertDTO,
  AlertState,
  SEVERITY_COLORS,
  SEVERITY_LABELS,
  Severity,
} from '@lews/shared-types';
import { api } from '@/lib/api';
import { cn } from '@/lib/cn';

export function AlertDetail({ alert }: { alert: AlertDTO }) {
  const qc = useQueryClient();
  const [reason, setReason] = useState('');
  const sev = SEVERITY_COLORS[alert.severity as Severity];

  const dismiss = useMutation({
    mutationFn: () => api.post(`/alerts/${alert.id}/dismiss`, { reason }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
  });

  return (
    <div className={cn('rounded-xl border p-4', sev.border, sev.bg)}>
      <div className="flex items-center justify-between">
        <span className={cn('text-lg font-bold', sev.text)}>
          {SEVERITY_LABELS[alert.severity as Severity]}
        </span>
        <span className="text-xs text-muted-foreground">{alert.state}</span>
      </div>
      <div className="mt-1 text-sm">{alert.message}</div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
        <div>First seen: {new Date(alert.first_seen_at).toLocaleString()}</div>
        <div>Last seen: {new Date(alert.last_seen_at).toLocaleString()}</div>
        {alert.acknowledged_at && (
          <div>Acked: {new Date(alert.acknowledged_at).toLocaleString()}</div>
        )}
        {alert.resolved_at && (
          <div>Resolved: {new Date(alert.resolved_at).toLocaleString()}</div>
        )}
      </div>

      {alert.trigger_payload && (
        <details className="mt-3">
          <summary className="cursor-pointer text-xs text-muted-foreground">
            Trigger payload
          </summary>
          <pre className="mt-1 max-h-40 overflow-auto rounded bg-background/50 p-2 text-xs">
            {JSON.stringify(alert.trigger_payload, null, 2)}
          </pre>
        </details>
      )}

      {alert.notification_log && alert.notification_log.length > 0 && (
        <details className="mt-3">
          <summary className="cursor-pointer text-xs text-muted-foreground">
            Notification log
          </summary>
          <pre className="mt-1 max-h-40 overflow-auto rounded bg-background/50 p-2 text-xs">
            {JSON.stringify(alert.notification_log, null, 2)}
          </pre>
        </details>
      )}

      {alert.state === AlertState.Open || alert.state === AlertState.Acknowledged ? (
        <div className="mt-3 flex gap-2">
          <input
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Dismiss reason (optional)"
            className="flex-1 rounded-md border border-input bg-background px-2 py-1 text-xs"
          />
          <button
            onClick={() => dismiss.mutate()}
            disabled={dismiss.isPending}
            className="rounded-md bg-muted px-3 py-1 text-xs text-muted-foreground hover:bg-muted/80"
          >
            Dismiss
          </button>
        </div>
      ) : null}
    </div>
  );
}
