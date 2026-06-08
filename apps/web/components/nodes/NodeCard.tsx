'use client';

import Link from 'next/link';
import { NodeDTO, NodeStatus, Severity, SEVERITY_COLORS, SEVERITY_LABELS, batteryPercent } from '@lews/shared-types';
import { cn } from '@/lib/cn';
import { NodeStatusDot } from './NodeStatusDot';
import { Battery } from 'lucide-react';

export function NodeCard({ node, severity = 0 }: { node: NodeDTO; severity?: Severity }) {
  const sev = SEVERITY_COLORS[severity];
  const pct = batteryPercent(node.battery_mv);
  return (
    <Link
      href={`/nodes/${node.id}`}
      className="block rounded-xl border border-border bg-card p-4 transition-colors hover:bg-accent/50"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <NodeStatusDot status={node.status} />
          <span className="font-semibold">{node.name ?? node.dev_eui}</span>
        </div>
        <span className={cn('text-xs font-bold', sev.text, sev.bg)}>
          {SEVERITY_LABELS[severity]}
        </span>
      </div>

      <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <Battery className="h-3 w-3" />
          <span>{pct != null ? `${pct}%` : '—'}</span>
        </div>
        <div>Last seen: {node.last_seen_at ? new Date(node.last_seen_at).toLocaleDateString() : 'Never'}</div>
      </div>
    </Link>
  );
}
