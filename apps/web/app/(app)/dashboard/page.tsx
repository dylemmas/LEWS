'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import {
  ALERTS,
  KPI,
  NODES,
  NODE_SEVERITIES,
  SITES,
  readingsForNode,
  siteNameFor,
  TENANT,
} from '@/lib/fixtures';
import AlertList from '@/components/alerts/AlertList';
import { Sparkline } from '@/components/charts/Sparkline';
import { NodeStatus, Severity, SEVERITY_LABELS, batteryPercent } from '@lews/shared-types';

// Leaflet touches `window` at module load — render only on the client.
const SiteMap = dynamic(() => import('@/components/map/SiteMap'), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center bg-slate-950 text-slate-500">
      Loading map…
    </div>
  ),
});

export default function DashboardPage() {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // KPIs computed once at module load (fixtures are deterministic).
  const kpi = KPI;

  return (
    <div className="flex h-full flex-col gap-6 p-6 lg:p-8">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Operations Dashboard</h1>
          <p className="text-sm text-slate-400">
            <span className="capitalize">{TENANT.slug}</span> · Bandung, West Java ·{' '}
            <span className="text-slate-500">demo data</span>
          · Updated {kpi.last_updated.slice(0, 10)}
          </p>
        </div>
        <div className="rounded border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-400">
          Last updated: {kpi.last_updated.slice(11, 19)} UTC
        </div>
      </header>

      {/* KPI cards */}
      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KPICard
          label="Active Alerts"
          value={kpi.active_alerts}
          accent="text-red-400"
          sub={`${kpi.critical_alerts} critical · ${kpi.warning_alerts} warning`}
        />
        <KPICard
          label="Online Nodes"
          value={`${kpi.online_nodes}/${kpi.total_nodes}`}
          accent="text-green-400"
          sub={`${kpi.total_nodes - kpi.online_nodes} degraded/offline`}
        />
        <KPICard
          label="24h Rainfall"
          value={`${kpi.rainfall_24h_mm} mm`}
          accent="text-sky-400"
          sub="5 sites, tipping-bucket"
        />
        <KPICard
          label="Avg Battery"
          value={`${batteryPercent(kpi.avg_battery_mv) ?? 0}%`}
          accent="text-amber-400"
          sub="LiSOCl2 primary cell"
        />
      </section>

      {/* Main grid: map + alerts */}
      <section className="grid flex-1 gap-6 lg:grid-cols-[3fr_2fr]">
        <div className="flex min-h-[420px] flex-col rounded border border-slate-800 bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
            <h2 className="text-sm font-semibold text-slate-200">Site map</h2>
            <a
              href="/map"
              className="text-xs font-medium text-sky-400 transition hover:text-sky-300"
            >
              Open full map →
            </a>
          </div>
          <div className="relative flex-1">
            <SiteMap
              nodes={NODES}
              severities={NODE_SEVERITIES}
              selectedNodeId={selectedNodeId}
              onNodeClick={setSelectedNodeId}
            />
          </div>
        </div>

        <div className="flex flex-col rounded border border-slate-800 bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
            <h2 className="text-sm font-semibold text-slate-200">Active alerts</h2>
            <span className="rounded-full border border-red-500/30 bg-red-500/10 px-2 py-0.5 text-xs font-medium text-red-400">
              {kpi.active_alerts} open
            </span>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            <AlertList
              alerts={ALERTS}
              onAck={() => {}}
              onResolve={() => {}}
            />
          </div>
        </div>
      </section>

      {/* Node grid */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200">
            All nodes ({NODES.length})
          </h2>
          <span className="text-xs text-slate-500">
            Click a node on the map to inspect
          </span>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {NODES.map((node, i) => {
            const severity = NODE_SEVERITIES[i] ?? Severity.Normal;
            const isSelected = node.id === selectedNodeId;
            const readings = readingsForNode(node.id);
            const rainSeries = readings.map((r) => r.rain_tips_15m);
            const batteryPct = batteryPercent(node.battery_mv);
            return (
              <button
                key={node.id}
                onClick={() => setSelectedNodeId(isSelected ? null : node.id)}
                className={`rounded border bg-slate-900 p-3 text-left transition ${
                  isSelected
                    ? 'border-sky-500 ring-1 ring-sky-500/40'
                    : 'border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="mb-2 flex items-center justify-between">
                  <div>
                    <div className="text-sm font-semibold text-white">
                      {node.name}
                    </div>
                    <div className="text-xs text-slate-500">
                      {siteNameFor(node.id)}
                    </div>
                  </div>
                  <SeverityDot severity={severity} />
                </div>

                <div className="mb-2 h-8 w-full">
                  <Sparkline data={rainSeries} color={sparklineColor(severity)} />
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className={statusColor(node.status)}>
                    <span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-current align-middle" />
                    {node.status}
                  </span>
                  <span className="text-slate-400">
                    {batteryPct != null ? `${batteryPct}%` : '—'}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </section>

      {/* Sites footer */}
      <section className="rounded border border-slate-800 bg-slate-900 p-4">
        <h2 className="mb-3 text-sm font-semibold text-slate-200">Sites</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {SITES.map((s) => {
            const count = NODES.filter((n) => n.site_id === s.id).length;
            return (
              <div
                key={s.id}
                className="rounded border border-slate-800 bg-slate-950/50 p-3"
              >
                <div className="text-sm font-medium text-white">{s.name}</div>
                <div className="text-xs text-slate-500">
                  {s.lat.toFixed(3)}, {s.lon.toFixed(3)}
                </div>
                <div className="mt-1 text-xs text-slate-400">
                  {count} nodes · {s.region}
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

function KPICard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent: string;
}) {
  return (
    <div className="rounded border border-slate-800 bg-slate-900 p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className={`mt-2 text-3xl font-bold ${accent}`}>{value}</div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}

function SeverityDot({ severity }: { severity: Severity }) {
  const colors: Record<Severity, string> = {
    [Severity.Normal]: 'bg-green-500',
    [Severity.Watch]: 'bg-blue-500',
    [Severity.Warning]: 'bg-yellow-500',
    [Severity.Critical]: 'bg-red-500 animate-pulse',
  };
  return (
    <div className="flex flex-col items-end">
      <div className={`h-3 w-3 rounded-full ${colors[severity]}`} />
      <div className="mt-1 text-[10px] uppercase tracking-wide text-slate-500">
        {SEVERITY_LABELS[severity]}
      </div>
    </div>
  );
}

function statusColor(status: NodeStatus): string {
  switch (status) {
    case NodeStatus.Online:
      return 'text-green-400';
    case NodeStatus.Degraded:
      return 'text-yellow-400';
    case NodeStatus.Offline:
      return 'text-slate-500';
    case NodeStatus.Maintenance:
      return 'text-blue-400';
    default:
      return 'text-slate-400';
  }
}

function sparklineColor(severity: Severity): string {
  switch (severity) {
    case Severity.Critical:
      return '#ef4444';
    case Severity.Warning:
      return '#eab308';
    case Severity.Watch:
      return '#3b82f6';
    default:
      return '#22c55e';
  }
}
