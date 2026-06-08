'use client';

import { useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import { Severity, SEVERITY_LABELS, batteryPercent } from '@lews/shared-types';
import {
  NODES,
  NODE_SEVERITIES,
  siteNameFor,
  readingsForNode,
} from '@/lib/fixtures';
import { Sparkline } from '@/components/charts/Sparkline';

// Dynamically import Leaflet to avoid SSR issues
const SiteMap = dynamic(() => import('@/components/map/SiteMap'), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center bg-slate-950">
      <div className="text-slate-500">Loading map…</div>
    </div>
  ),
});

export default function MapPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selectedIndex = useMemo(
    () => (selectedId ? NODES.findIndex((n) => n.id === selectedId) : -1),
    [selectedId]
  );
  const selected = selectedIndex >= 0 ? NODES[selectedIndex] : null;
  const selectedBatteryPct = selected ? batteryPercent(selected.battery_mv) : null;
  const selectedSeverity =
    selectedIndex >= 0 ? NODE_SEVERITIES[selectedIndex] : null;

  const counts = useMemo(() => {
    const out = { critical: 0, warning: 0, watch: 0, normal: 0 };
    for (const s of NODE_SEVERITIES) {
      if (s === Severity.Critical) out.critical++;
      else if (s === Severity.Warning) out.warning++;
      else if (s === Severity.Watch) out.watch++;
      else out.normal++;
    }
    return out;
  }, []);

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b border-slate-800 bg-slate-900 px-6 py-4">
        <div>
          <h1 className="text-xl font-bold text-white">Live Map</h1>
          <p className="text-sm text-slate-400">
            {NODES.length} nodes across 5 sites · Bandung, West Java
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <Legend color="bg-red-500" label="Critical" count={counts.critical} />
          <Legend color="bg-yellow-500" label="Warning" count={counts.warning} />
          <Legend color="bg-blue-500" label="Watch" count={counts.watch} />
          <Legend color="bg-green-500" label="Normal" count={counts.normal} />
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <div className="relative flex-1 bg-slate-950">
          <SiteMap
            nodes={NODES}
            severities={NODE_SEVERITIES}
            selectedNodeId={selectedId}
            onNodeClick={setSelectedId}
          />
        </div>

        {/* Side panel — shows on selection */}
        {selected && selectedSeverity !== null ? (
          <aside className="w-[360px] overflow-y-auto border-l border-slate-800 bg-slate-900 p-5">
            <div className="mb-4 flex items-start justify-between">
              <div>
                <div className="text-xs uppercase tracking-wide text-slate-500">
                  {siteNameFor(selected.id)}
                </div>
                <h2 className="text-lg font-bold text-white">{selected.name}</h2>
                <div className="mt-1 font-mono text-xs text-slate-500">
                  {selected.dev_eui}
                </div>
              </div>
              <button
                onClick={() => setSelectedId(null)}
                className="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-white"
                aria-label="Close panel"
              >
                ✕
              </button>
            </div>

            <div className="mb-4 rounded border border-slate-800 bg-slate-950/50 p-3">
              <div className="text-xs uppercase tracking-wide text-slate-500">
                Current severity
              </div>
              <div
                className={`mt-1 text-2xl font-bold ${severityTextColor(
                  selectedSeverity
                )}`}
              >
                {SEVERITY_LABELS[selectedSeverity]}
              </div>
            </div>

            <div className="mb-4 grid grid-cols-2 gap-3 text-sm">
              <Field label="Status" value={selected.status} />
              <Field
                label="Battery"
                value={selectedBatteryPct != null ? `${selectedBatteryPct}%` : '—'}
              />
              <Field
                label="Position"
                value={`${selected.lat.toFixed(4)}, ${selected.lon.toFixed(4)}`}
              />
              <Field
                label="Last seen"
                value={new Date(selected.last_seen_at).toISOString().slice(11, 19) + ' UTC'}
              />
            </div>

            <div className="mb-4">
              <div className="mb-2 text-xs uppercase tracking-wide text-slate-500">
                Rain (last 24h, 15-min tips)
              </div>
              <div className="h-24 rounded border border-slate-800 bg-slate-950/50 p-2">
                <Sparkline
                  data={readingsForNode(selected.id).map((r) => r.rain_tips_15m)}
                  color={severityColor(selectedSeverity)}
                />
              </div>
            </div>

            <div>
              <div className="mb-2 text-xs uppercase tracking-wide text-slate-500">
                Acceleration magnitude (last 24h, g)
              </div>
              <div className="h-24 rounded border border-slate-800 bg-slate-950/50 p-2">
                <Sparkline
                  data={readingsForNode(selected.id).map((r) => r.accel_magnitude_g)}
                  color={severityColor(selectedSeverity)}
                />
              </div>
            </div>

            <a
              href="/dashboard"
              className="mt-5 block w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-center text-sm font-medium text-slate-200 transition hover:bg-slate-700"
            >
              Back to dashboard
            </a>
          </aside>
        ) : (
          <aside className="hidden w-[320px] overflow-y-auto border-l border-slate-800 bg-slate-900 p-5 md:block">
            <h2 className="text-sm font-semibold text-slate-200">
              How to use this map
            </h2>
            <ul className="mt-3 space-y-2 text-sm text-slate-400">
              <li>· Click any marker to inspect a node</li>
              <li>· Markers are colored by current severity</li>
              <li>· The selected node&apos;s panel shows 24h trends</li>
            </ul>
            <div className="mt-6 rounded border border-slate-800 bg-slate-950/50 p-3 text-xs text-slate-500">
              Demo data is loaded from a static fixture set. Backend services are
              not required for this view.
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}

function Legend({
  color,
  label,
  count,
}: {
  color: string;
  label: string;
  count: number;
}) {
  return (
    <div className="flex items-center gap-1.5 rounded border border-slate-800 bg-slate-950 px-2 py-1">
      <div className={`h-2 w-2 rounded-full ${color}`} />
      <span className="text-slate-400">{label}</span>
      <span className="font-mono text-slate-500">{count}</span>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-0.5 text-sm text-slate-200">{value}</div>
    </div>
  );
}

function severityTextColor(s: Severity): string {
  switch (s) {
    case Severity.Critical:
      return 'text-red-400';
    case Severity.Warning:
      return 'text-yellow-400';
    case Severity.Watch:
      return 'text-blue-400';
    default:
      return 'text-green-400';
  }
}

function severityColor(s: Severity): string {
  switch (s) {
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
