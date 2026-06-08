# Landslide EWS — Demo Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a locally-runnable Next.js 14 dashboard at `apps/web/` populated with deterministic fixtures, suitable for a presentation demo. The full backend, auth, ML, WebSockets, and simulator are deferred.

**Architecture:** Pure-frontend rebuild of the dashboard. New `apps/web/lib/fixtures.ts` is the single source of synthetic data (1 tenant, 5 sites, 15 nodes, 24h of sparklines, 3 alerts, 1 KPI summary). Demo pages import fixtures directly — no `fetch`, no axios, no NextAuth, no Socket.IO. Auth gate is removed; `/` redirects straight to `/dashboard`. Two hero pages (`/dashboard`, `/map`) get real fixture data; six other routes render a "Coming soon" panel. The pre-existing `SiteMap` bug (hardcoded `severity = 0`) is fixed as part of this work.

**Tech Stack:** Next.js 14.1 (App Router), React 18, TypeScript, Tailwind 3.4, Recharts 2.15, Leaflet 1.9 + react-leaflet 4.2, lucide-react icons, `@lews/shared-types` workspace package (DTOs + severity enums).

---

## File Structure

**New files:**
- `apps/web/lib/fixtures.ts` — deterministic synthetic data (1 module, ~150 lines)

**Modified files (in dependency order):**
1. `apps/web/lib/api.ts` — add `API_URL` named export (1 line)
2. `apps/web/components/map/SiteMap.tsx` — fix `severity = 0` bug, add `severities` prop, add `onMarkerClick` prop
3. `apps/web/app/(app)/layout.tsx` — strip auth gate, hardcode demo user
4. `apps/web/app/(app)/dashboard/page.tsx` — rewrite to read fixtures
5. `apps/web/app/(app)/map/page.tsx` — rewrite to read fixtures, add click side-panel
6. 6 stub pages (see Task 7) — replace with "Coming soon" panel

**Untouched (deferred to follow-up):** all `apps/api/`, `services/simulator/`, `infra/timescaledb/`, `infra/seed/`, docker-compose, real auth, WebSocket plumbing.

**Why this decomposition:** each modified file has one job. The fixtures module is the only new file because it is the only new responsibility. The stub pages share an inline template; we extract a `ComingSoon` component only if it exceeds 10 lines (CLAUDE.md: no abstractions for single-use code).

---

## Task 1: Add `API_URL` export to `lib/api.ts`

**Files:**
- Modify: `apps/web/lib/api.ts:46` (current `export { api };` line)

- [ ] **Step 1: Verify the bug**

Open `apps/web/lib/api.ts`. Confirm line 46 is `export { api };` and that `API_URL` is NOT exported. Also confirm `apps/web/app/(app)/layout.tsx:5` and `apps/web/app/(app)/dashboard/page.tsx:4` both have `import { API_URL } from '@/lib/api';` (these imports will be removed by later tasks but must resolve to a real export for the build to succeed in between).

- [ ] **Step 2: Add the missing export**

Edit `apps/web/lib/api.ts`. After the `import axios from 'axios';` line (line 1), add:

```ts
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

Leave everything else unchanged. The existing axios `baseURL` on line 4 (`process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'`) is fine — it produces the same base URL the legacy `fetch` callers compute as `${API_URL}/v1`.

- [ ] **Step 3: Verify the import resolves**

Open `apps/web/app/(app)/layout.tsx:5` in your editor. The `API_URL` import should no longer be marked red by TypeScript. (You can defer the actual `pnpm dev` run to Task 8 — at this point, just confirm the file compiles in your editor if you have TS language server running.)

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews"
git add apps/web/lib/api.ts
git commit -m "fix(web): export API_URL from lib/api"
```

---

## Task 2: Create `lib/fixtures.ts` (deterministic synthetic data)

**Files:**
- Create: `apps/web/lib/fixtures.ts`

- [ ] **Step 1: Create the file with the full contents below**

Create `apps/web/lib/fixtures.ts` with this exact content:

```ts
// Deterministic synthetic data for the demo dashboard. No backend required.
// Reuses DTOs from @lews/shared-types (which is the same shape the FastAPI
// backend produces), so pages can be migrated to live data with one import swap.

import {
  AlertState,
  NodeStatus,
  Severity,
  TenantPlan,
  type AlertDTO,
  type KPISummary,
  type NodeDTO,
  type SiteDTO,
  type TenantDTO,
  type UserDTO,
} from '@lews/shared-types';

// --- Seeded PRNG (mulberry32) for determinism -----------------------------
function makeRng(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rng = makeRng(42);
const pick = <T>(arr: readonly T[]) => arr[Math.floor(rng() * arr.length)];
const between = (lo: number, hi: number) => lo + Math.floor(rng() * (hi - lo + 1));

// --- Tenant ---------------------------------------------------------------
export const tenant: TenantDTO = {
  id: '11111111-1111-1111-1111-111111111111',
  slug: 'acme',
  plan: TenantPlan.Pro,
  created_at: '2026-01-15T08:00:00Z',
};

// A display-only user for the demo. No auth, just shows in the sidebar.
export const demoUser: UserDTO = {
  id: '22222222-2222-2222-2222-222222222222',
  tenant_id: tenant.id,
  email: 'admin@lews.dev',
  full_name: 'Demo User',
  role: 'admin' as UserDTO['role'],
  phone_e164: null,
  created_at: tenant.created_at,
};

// --- Sites (Bandung) ------------------------------------------------------
const SITE_DEFS = [
  { name: 'Cimenyan',    lat: -6.85,  lon: 107.65 },
  { name: 'Lembang',     lat: -6.82,  lon: 107.62 },
  { name: 'Pangalengan', lat: -7.18,  lon: 107.55 },
  { name: 'Ciwidey',     lat: -7.15,  lon: 107.48 },
  { name: 'Cikalong',    lat: -6.92,  lon: 107.58 },
] as const;

export const sites: SiteDTO[] = SITE_DEFS.map((s, i) => ({
  id: `s${i + 1}-${s.name.toLowerCase()}`,
  tenant_id: tenant.id,
  name: s.name,
  region: 'Bandung',
  lat: s.lat,
  lon: s.lon,
  created_at: tenant.created_at,
}));

const sitesById = new Map(sites.map((s) => [s.id, s]));

// --- Nodes (3 per site = 15) ----------------------------------------------
const STATUS_PLAN: NodeStatus[] = [
  NodeStatus.Online, NodeStatus.Online, NodeStatus.Online,    // site 1
  NodeStatus.Online, NodeStatus.Online, NodeStatus.Online,    // site 2
  NodeStatus.Online, NodeStatus.Online, NodeStatus.Online,    // site 3
  NodeStatus.Online, NodeStatus.Online, NodeStatus.Online,    // site 4
  NodeStatus.Online, NodeStatus.Degraded, NodeStatus.Offline, // site 5
];
// Result: 13 online, 1 degraded, 1 offline

// Visual severity distribution: 3 critical, 2 warning, 1 watch, 9 normal
const SEVERITY_PLAN: Severity[] = [
  Severity.Critical, Severity.Warning, Severity.Normal, // site 1
  Severity.Critical, Severity.Normal,  Severity.Normal,  // site 2
  Severity.Warning,  Severity.Watch,   Severity.Normal,  // site 3
  Severity.Normal,   Severity.Normal,  Severity.Critical,// site 4
  Severity.Normal,   Severity.Normal,  Severity.Normal,  // site 5
];

const now = () => new Date().toISOString();

export const nodes: NodeDTO[] = sites.flatMap((site, sIdx) =>
  [1, 2, 3].map((n) => {
    const idx = sIdx * 3 + (n - 1);
    return {
      id: `n${idx + 1}-${site.name.toLowerCase()}-${n}`,
      tenant_id: tenant.id,
      site_id: site.id,
      dev_eui: `01020304${(idx + 1).toString(16).padStart(2, '0')}`,
      name: `${site.name} Node ${n}`,
      status: STATUS_PLAN[idx],
      last_seen_at: STATUS_PLAN[idx] === NodeStatus.Offline
        ? null
        : new Date(Date.now() - between(1, 5) * 60_000).toISOString(),
      battery_mv: STATUS_PLAN[idx] === NodeStatus.Offline ? null : between(3200, 4200),
      lat: site.lat + (rng() - 0.5) * 0.005,
      lon: site.lon + (rng() - 0.5) * 0.005,
      hardware_version: 'rev-B',
      firmware_version: '1.4.2',
      created_at: tenant.created_at,
    };
  })
);

const nodesById = new Map(nodes.map((n) => [n.id, n]));

export const nodeSeverities: Record<string, Severity> = Object.fromEntries(
  nodes.map((n, i) => [n.id, SEVERITY_PLAN[i]])
);

// --- Sparklines (24 hourly rain_tips per node) ---------------------------
export const nodeSparklines: Record<string, number[]> = Object.fromEntries(
  nodes.map((n) => {
    const sev = nodeSeverities[n.id] ?? Severity.Normal;
    const base = sev === Severity.Critical ? 60 : sev === Severity.Warning ? 35 : sev === Severity.Watch ? 18 : 5;
    const points: number[] = [];
    for (let h = 0; h < 24; h++) {
      const r = rng();
      // Simulate a rain burst in the last 6 hours for higher-severity nodes
      const burstBoost = h >= 18 && sev >= Severity.Warning ? base * 1.5 : 0;
      points.push(Math.max(0, Math.round(base + burstBoost + r * 10 - 3)));
    }
    return [n.id, points];
  })
);

// --- Alerts (1 Critical, 1 Warning, 1 Watch) ------------------------------
const ALERT_PLAN: Array<{ severity: Severity; minutesAgo: number; title: string; message: string }> = [
  {
    severity: Severity.Critical,
    minutesAgo: 30,
    title: 'Critical tilt and rainfall at Cimenyan Node 1',
    message: 'Tilt delta exceeded 500 dddeg with sustained rainfall > 40 tips/15m. Immediate evacuation review recommended.',
  },
  {
    severity: Severity.Warning,
    minutesAgo: 120,
    title: 'Warning: Pangalengan Node 1 showing rising crack displacement',
    message: 'Crack sensor showing +60 mm displacement over the last 2 hours. Monitor closely.',
  },
  {
    severity: Severity.Watch,
    minutesAgo: 360,
    title: 'Watch: Lembang Node 2 vibration baseline elevated',
    message: 'Accel RMS running 15% above weekly baseline. No breach yet.',
  },
];

export const alerts: AlertDTO[] = ALERT_PLAN.map((a, i) => {
  // Pick a node whose severity matches, for visual coherence
  const candidate = nodes.find((n) => nodeSeverities[n.id] === a.severity) ?? nodes[i];
  const site = sitesById.get(candidate.site_id)!;
  const firstSeen = new Date(Date.now() - a.minutesAgo * 60_000).toISOString();
  const lastSeen = new Date(Date.now() - Math.max(1, a.minutesAgo - 15) * 60_000).toISOString();
  return {
    id: `al${i + 1}`,
    tenant_id: tenant.id,
    node_id: candidate.id,
    site_id: site.id,
    severity: a.severity,
    state: AlertState.Open,
    title: a.title,
    message: a.message,
    trigger_payload: null,
    first_seen_at: firstSeen,
    last_seen_at: lastSeen,
    acknowledged_at: null,
    acknowledged_by: null,
    resolved_at: null,
    resolved_by: null,
    dismissed_at: null,
    dismissed_by: null,
    dismiss_reason: null,
    ml_prob: a.severity === Severity.Critical ? 0.87 : a.severity === Severity.Warning ? 0.61 : 0.34,
    notification_log: [],
  };
});

// --- KPI summary ---------------------------------------------------------
const onlineCount = nodes.filter((n) => n.status === NodeStatus.Online).length;
const totalRainTips = Object.values(nodeSparklines).reduce(
  (acc, arr) => acc + arr.reduce((s, v) => s + v, 0),
  0
);
const batteryNodes = nodes.filter((n) => n.battery_mv != null) as Array<NodeDTO & { battery_mv: number }>;
const avgBattery = Math.round(
  batteryNodes.reduce((s, n) => s + n.battery_mv, 0) / batteryNodes.length
);

export const kpi: KPISummary = {
  active_alerts: alerts.length,
  critical_alerts: alerts.filter((a) => a.severity === Severity.Critical).length,
  warning_alerts: alerts.filter((a) => a.severity === Severity.Warning).length,
  online_nodes: onlineCount,
  total_nodes: nodes.length,
  avg_battery_mv: avgBattery,
  rainfall_24h_mm: Math.round(totalRainTips * 0.3), // tips → mm approximation
  last_updated: now(),
};

// --- Helpers used by pages ------------------------------------------------
export const getSiteById = (id: string) => sitesById.get(id);
export const getNodeById = (id: string) => nodesById.get(id);
```

- [ ] **Step 2: Verify TypeScript compiles**

Run:
```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews"
pnpm --filter lews-web exec tsc --noEmit
```

Expected: zero errors. (If you get `Cannot find module '@lews/shared-types'`, ensure the workspace is installed: `pnpm install` from the repo root first.)

- [ ] **Step 3: Spot-check the generated data**

Run this one-liner in Node (from the repo root) to confirm shape and counts:
```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews"
node -e "const f = require('./apps/web/lib/fixtures.ts');" 2>&1 | head -5
```

Expected: an error about `.ts` (Node can't load TS directly) — that's fine; the real verification is the TS check in step 2. If you want a quick runtime sanity check, temporarily add `export const debug = { siteCount: sites.length, nodeCount: nodes.length, alertCount: alerts.length };` and verify in the dev server console in Task 8, then remove it.

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews"
git add apps/web/lib/fixtures.ts
git commit -m "feat(web): add deterministic fixture data for demo"
```

---

## Task 3: Fix `SiteMap` severity bug and add click handler prop

**Files:**
- Modify: `apps/web/components/map/SiteMap.tsx`

- [ ] **Step 1: Read the current file**

Open `apps/web/components/map/SiteMap.tsx`. Confirm:
- Line 18–23: local `SEVERITY_COLORS` Record (hex values) — keep
- Line 25–27: `interface SiteMapProps { nodes: NodeDTO[]; }` — extend
- Line 56: `const severity = 0; // TODO: fetch latest reading severity` — fix

- [ ] **Step 2: Extend the props interface**

Replace lines 25–27 with:
```tsx
import type { NodeDTO, Severity } from '@lews/shared-types';

interface SiteMapProps {
  nodes: NodeDTO[];
  severities?: Record<string, Severity>;
  onMarkerClick?: (nodeId: string) => void;
}
```

(If `NodeDTO` is already imported as `import type { NodeDTO } from '@lews/shared-types';` on line 5, just add `, Severity` to that line instead of a new import.)

- [ ] **Step 3: Pass props through to `SeverityMarker`**

Update the `SiteMap` function signature and the `SeverityMarker` call:

```tsx
export default function SiteMap({ nodes, severities, onMarkerClick }: SiteMapProps) {
  // Default center to Bandung if no nodes
  const center: [number, number] =
    nodes.length > 0
      ? [nodes[0]!.lat, nodes[0]!.lon]
      : [-6.9175, 107.6191];

  return (
    <MapContainer
      center={center}
      zoom={11}
      className="h-full w-full"
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {nodes.map((node) => (
        <SeverityMarker
          key={node.id}
          node={node}
          severity={severities?.[node.id] ?? 0}
          onClick={onMarkerClick}
        />
      ))}
    </MapContainer>
  );
}
```

- [ ] **Step 4: Fix the severity and wire the click handler**

Replace the `SeverityMarker` function (currently lines 54–100) with:

```tsx
function SeverityMarker({
  node,
  severity,
  onClick,
}: {
  node: NodeDTO;
  severity: Severity;
  onClick?: (nodeId: string) => void;
}) {
  const color = SEVERITY_COLORS[severity] ?? SEVERITY_COLORS[0];

  const icon = L.divIcon({
    className: 'custom-div-icon',
    html: `<div style="
      background-color: ${color};
      width: 24px;
      height: 24px;
      border-radius: 50%;
      border: 3px solid white;
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });

  return (
    <Marker
      position={[node.lat, node.lon]}
      icon={icon}
      eventHandlers={{ click: () => onClick?.(node.id) }}
    >
      <Popup>
        <div className="min-w-[200px]">
          <h3 className="mb-1 font-semibold">{node.name || node.dev_eui}</h3>
          <p className="mb-1 text-sm text-slate-600">{node.dev_eui}</p>
          <p className="mb-1 text-sm">
            Status:{' '}
            <span className="capitalize">{node.status}</span>
          </p>
          {node.battery_mv && (
            <p className="mb-1 text-sm">
              Battery: {(node.battery_mv / 1000).toFixed(2)}V
            </p>
          )}
          <a
            href={`/nodes/${node.id}`}
            className="mt-2 block rounded bg-sky-600 px-3 py-1 text-center text-sm font-medium text-white hover:bg-sky-700"
          >
            View Details
          </a>
        </div>
      </Popup>
    </Marker>
  );
}
```

Note: the `SEVERITY_COLORS[severity]` lookup previously used `Record<number, string>` (keyed by 0/1/2/3 numeric). The `severity` parameter is now typed `Severity` (an enum) which is a number at runtime, so the lookup still works. The `?? SEVERITY_COLORS[0]` is a defensive fallback for any value out of range.

- [ ] **Step 5: Type-check**

```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews"
pnpm --filter lews-web exec tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 6: Commit**

```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews"
git add apps/web/components/map/SiteMap.tsx
git commit -m "fix(web): SiteMap marker severity + add click handler prop"
```

---

## Task 4: Strip auth gate from `(app)/layout.tsx`

**Files:**
- Modify: `apps/web/app/(app)/layout.tsx`

- [ ] **Step 1: Read the current file**

Open `apps/web/app/(app)/layout.tsx`. The current file (99 lines) imports `useEffect`, `usePathname`, `useRouter` from `next/navigation` and `API_URL` from `@/lib/api`.

- [ ] **Step 2: Delete the auth-redirect `useEffect`**

Delete lines 11–16 (the `useEffect(() => { const token = ...; if (!token) router.push('/login'); }, [router]);` block).

Also delete the now-unused `useRouter` import on line 3 (keep `usePathname` on line 2 — still used by the inline nav links).

If TypeScript flags `API_URL` as unused after the next task removes its import from layout, you can drop the `import { API_URL }` line. But for now keep the import — Task 5 hasn't removed the dashboard's import yet.

- [ ] **Step 3: Replace the localStorage user display with hardcoded values**

In the bottom-of-sidebar block (currently lines 71–87), the display reads `localStorage.getItem('user')`. Replace it with a hardcoded string. Find:

```tsx
<div className="text-sm">
  <div className="font-medium text-slate-200">
    {typeof window !== 'undefined' && JSON.parse(localStorage.getItem('user') || '{}').full_name || 'User'}
  </div>
  <div className="text-xs text-slate-500">
    {typeof window !== 'undefined' && JSON.parse(localStorage.getItem('user') || '{}').email}
  </div>
</div>
<button
  onClick={() => {
    localStorage.clear();
    router.push('/login');
  }}
  className="text-sm text-slate-500 hover:text-red-400"
>
  Logout
</button>
```

Replace with:

```tsx
<div className="text-sm">
  <div className="font-medium text-slate-200">Demo User</div>
  <div className="text-xs text-slate-500">admin@lews.dev</div>
</div>
<button
  type="button"
  disabled
  className="cursor-not-allowed text-sm text-slate-600"
  title="Auth disabled in demo mode"
>
  Logout
</button>
```

- [ ] **Step 4: Type-check**

```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews"
pnpm --filter lews-web exec tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews"
git add apps/web/app/\(app\)/layout.tsx
git commit -m "feat(web): strip auth gate from app layout (demo mode)"
```

---

## Task 5: Rewrite `dashboard/page.tsx` to read fixtures

**Files:**
- Modify: `apps/web/app/(app)/dashboard/page.tsx` (full rewrite)

- [ ] **Step 1: Replace the entire file contents**

Open `apps/web/app/(app)/dashboard/page.tsx` and **replace the entire file** with:

```tsx
import { SEVERITY_COLORS, SEVERITY_LABELS, type Severity } from '@lews/shared-types';
import Link from 'next/link';
import { SiteMap } from '@/components/map/SiteMap';
import { Sparkline } from '@/components/charts/Sparkline';
import { NodeStatusDot } from '@/components/nodes/NodeStatusDot';
import {
  alerts,
  kpi,
  nodeSeverities,
  nodeSparklines,
  nodes,
  sites,
  getSiteById,
} from '@/lib/fixtures';

export default function DashboardPage() {
  return (
    <div className="min-h-full bg-slate-950 p-8 text-slate-100">
      {/* Header */}
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-slate-400">
            Last updated: {new Date(kpi.last_updated).toLocaleString()}
          </p>
        </div>
        <Link
          href="/map"
          className="rounded border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800"
        >
          Open full map →
        </Link>
      </div>

      {/* KPI cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard title="Active Alerts"   value={kpi.active_alerts}                                  color="text-red-400" />
        <KpiCard title="Critical Alerts" value={kpi.critical_alerts}                                color="text-red-500" />
        <KpiCard title="Online Nodes"    value={`${kpi.online_nodes} / ${kpi.total_nodes}`}        color="text-green-400" />
        <KpiCard title="24h Rainfall"    value={`${kpi.rainfall_24h_mm} mm`}                       color="text-sky-400" />
      </div>

      {/* Map preview + alerts */}
      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <section>
          <h2 className="mb-3 text-lg font-semibold">Live Map</h2>
          <div className="h-80 overflow-hidden rounded border border-slate-800">
            <SiteMap nodes={nodes} severities={nodeSeverities} />
          </div>
        </section>
        <section>
          <h2 className="mb-3 text-lg font-semibold">Active Alerts</h2>
          <div className="space-y-2">
            {alerts.map((a) => {
              const sev = a.severity as Severity;
              const c = SEVERITY_COLORS[sev];
              const node = nodes.find((n) => n.id === a.node_id);
              const site = getSiteById(a.site_id);
              return (
                <div
                  key={a.id}
                  className={`rounded border p-4 ${c.bg} ${c.border}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className={`font-medium ${c.text}`}>{a.title}</div>
                      <div className="mt-1 text-sm text-slate-300">{a.message}</div>
                      <div className="mt-2 text-xs text-slate-500">
                        {site?.name} · {node?.name ?? a.node_id} ·{' '}
                        {new Date(a.first_seen_at).toLocaleString()}
                      </div>
                    </div>
                    <span className={`shrink-0 rounded px-2 py-0.5 text-xs font-bold ${c.text} ${c.bg}`}>
                      {SEVERITY_LABELS[sev]}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>

      {/* Node grid */}
      <h2 className="mb-3 mt-10 text-lg font-semibold">Nodes ({nodes.length})</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {nodes.map((node) => {
          const sev = (nodeSeverities[node.id] ?? 0) as Severity;
          const c = SEVERITY_COLORS[sev];
          const site = getSiteById(node.site_id);
          const spark = nodeSparklines[node.id] ?? [];
          return (
            <div
              key={node.id}
              className="rounded border border-slate-800 bg-slate-900 p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <NodeStatusDot status={node.status} />
                  <span className="font-semibold text-slate-100">{node.name}</span>
                </div>
                <span className={`rounded px-2 py-0.5 text-xs font-bold ${c.text} ${c.bg} ${c.border}`}>
                  {SEVERITY_LABELS[sev]}
                </span>
              </div>
              <div className="mt-1 text-xs text-slate-500">
                {site?.name} · {node.dev_eui}
              </div>
              <div className="mt-3 flex items-end justify-between gap-2">
                <div>
                  <div className="text-xs text-slate-400">Battery</div>
                  <div className="text-sm font-medium text-slate-200">
                    {node.battery_mv ? `${(node.battery_mv / 1000).toFixed(2)}V` : '—'}
                  </div>
                </div>
                <div className="h-10 w-32">
                  <Sparkline data={spark} color={c.text.replace('text-', '#') || '#22c55e'} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer note */}
      <p className="mt-10 text-center text-xs text-slate-600">
        Showing {sites.length} sites · {nodes.length} nodes · demo data
      </p>
    </div>
  );
}

function KpiCard({ title, value, color }: { title: string; value: string | number; color: string }) {
  return (
    <div className="rounded border border-slate-800 bg-slate-900 p-5">
      <div className="text-sm text-slate-400">{title}</div>
      <div className={`mt-2 text-3xl font-bold ${color}`}>{value}</div>
    </div>
  );
}
```

- [ ] **Step 2: Check the `Sparkline` prop shape**

Open `apps/web/components/charts/Sparkline.tsx`. Confirm its `data` prop is `number[]` and (optionally) accepts a `color` prop. If `Sparkline` only accepts `data` (no color override), change this line in the dashboard:

```tsx
<Sparkline data={spark} color={c.text.replace('text-', '#') || '#22c55e'} />
```

to:

```tsx
<Sparkline data={spark} />
```

and accept the default color. (Read the file to confirm before adjusting.)

- [ ] **Step 3: Type-check**

```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews"
pnpm --filter lews-web exec tsc --noEmit
```

Expected: zero errors. If `Sparkline` has a different prop name, fix the call site and re-run.

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews"
git add apps/web/app/\(app\)/dashboard/page.tsx
git commit -m "feat(web): dashboard reads fixtures (no API calls)"
```

---

## Task 6: Rewrite `map/page.tsx` with click side-panel

**Files:**
- Modify: `apps/web/app/(app)/map/page.tsx` (full rewrite)

- [ ] **Step 1: Replace the entire file contents**

Open `apps/web/app/(app)/map/page.tsx` and **replace the entire file** with:

```tsx
'use client';

import { useState } from 'react';
import {
  SEVERITY_COLORS,
  SEVERITY_LABELS,
  type Severity,
} from '@lews/shared-types';
import { SiteMap } from '@/components/map/SiteMap';
import { Sparkline } from '@/components/charts/Sparkline';
import { NodeStatusDot } from '@/components/nodes/NodeStatusDot';
import {
  getSiteById,
  nodeSeverities,
  nodeSparklines,
  nodes,
} from '@/lib/fixtures';

export default function MapPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = selectedId ? nodes.find((n) => n.id === selectedId) : null;
  const selectedSev = selected ? ((nodeSeverities[selected.id] ?? 0) as Severity) : null;
  const selectedSite = selected ? getSiteById(selected.site_id) : null;
  const selectedSpark = selected ? (nodeSparklines[selected.id] ?? []) : [];

  return (
    <div className="relative h-full w-full bg-slate-950">
      <div className="absolute inset-0">
        <SiteMap
          nodes={nodes}
          severities={nodeSeverities}
          onMarkerClick={setSelectedId}
        />
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-[400] rounded border border-slate-700 bg-slate-900/90 p-3 text-xs text-slate-200 backdrop-blur">
        <div className="mb-2 font-semibold">Severity</div>
        {([0, 1, 2, 3] as Severity[]).map((s) => {
          const c = SEVERITY_COLORS[s];
          return (
            <div key={s} className="flex items-center gap-2 py-0.5">
              <span className={`inline-block h-3 w-3 rounded-full ${c.bg} ${c.border}`} />
              {SEVERITY_LABELS[s]}
            </div>
          );
        })}
      </div>

      {/* Side panel */}
      {selected && selectedSev !== null && selectedSite && (
        <aside className="absolute right-0 top-0 z-[500] h-full w-96 overflow-y-auto border-l border-slate-700 bg-slate-900 p-6 text-slate-100 shadow-2xl">
          <button
            type="button"
            onClick={() => setSelectedId(null)}
            className="mb-4 text-sm text-slate-400 hover:text-slate-200"
          >
            ← Close
          </button>
          <h2 className="text-xl font-bold">{selected.name}</h2>
          <div className="mt-1 text-sm text-slate-400">
            {selectedSite.name} · {selected.dev_eui}
          </div>

          <div className="mt-4 flex items-center gap-3">
            <NodeStatusDot status={selected.status} />
            <span className={`rounded px-2 py-0.5 text-xs font-bold ${SEVERITY_COLORS[selectedSev].text} ${SEVERITY_COLORS[selectedSev].bg} ${SEVERITY_COLORS[selectedSev].border}`}>
              {SEVERITY_LABELS[selectedSev]}
            </span>
          </div>

          <dl className="mt-6 grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-slate-400">Battery</dt>
              <dd className="mt-1 font-medium">
                {selected.battery_mv ? `${(selected.battery_mv / 1000).toFixed(2)}V` : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-slate-400">Last seen</dt>
              <dd className="mt-1 font-medium">
                {selected.last_seen_at
                  ? new Date(selected.last_seen_at).toLocaleString()
                  : 'Never'}
              </dd>
            </div>
            <div>
              <dt className="text-slate-400">Latitude</dt>
              <dd className="mt-1 font-mono">{selected.lat.toFixed(4)}</dd>
            </div>
            <div>
              <dt className="text-slate-400">Longitude</dt>
              <dd className="mt-1 font-mono">{selected.lon.toFixed(4)}</dd>
            </div>
          </dl>

          <div className="mt-6">
            <div className="mb-2 text-sm text-slate-400">24h rain (hourly tips)</div>
            <div className="h-16 rounded border border-slate-800 bg-slate-950 p-2">
              <Sparkline data={selectedSpark} />
            </div>
          </div>

          <button
            type="button"
            disabled
            className="mt-8 w-full cursor-not-allowed rounded border border-slate-700 px-4 py-2 text-sm text-slate-500"
            title="Full node details coming soon"
          >
            View full details
          </button>
        </aside>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews"
pnpm --filter lews-web exec tsc --noEmit
```

Expected: zero errors. If `Sparkline` errors on `data` only (no color), remove the color override (per Task 5 step 2).

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews"
git add apps/web/app/\(app\)/map/page.tsx
git commit -m "feat(web): map page with click side-panel (no API calls)"
```

---

## Task 7: Replace 6 stub pages with "Coming soon" panel

**Files:**
- Modify: `apps/web/app/(app)/sites/page.tsx`
- Modify: `apps/web/app/(app)/sites/[id]/page.tsx`
- Modify: `apps/web/app/(app)/nodes/page.tsx`
- Modify: `apps/web/app/(app)/nodes/[id]/page.tsx`
- Modify: `apps/web/app/(app)/alerts/page.tsx`
- Modify: `apps/web/app/(app)/settings/page.tsx`

- [ ] **Step 1: Replace each stub page**

For each of the 6 files above, **replace the entire file contents** with:

```tsx
import Link from 'next/link';

export default function Page() {
  return (
    <div className="flex h-full items-center justify-center bg-slate-950 p-8 text-slate-100">
      <div className="max-w-md text-center">
        <div className="mb-4 text-5xl">🚧</div>
        <h1 className="mb-2 text-2xl font-bold">Coming soon</h1>
        <p className="mb-6 text-slate-400">
          This page is part of the full build. The demo focuses on the Dashboard and Map.
        </p>
        <Link
          href="/dashboard"
          className="inline-block rounded bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700"
        >
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
```

For `sites/[id]/page.tsx` and `nodes/[id]/page.tsx`, the file structure is the same — just paste the same content. The `params` prop for dynamic routes is not needed in this stub.

- [ ] **Step 2: Verify the sidebar still links work**

Open `apps/web/app/(app)/layout.tsx` and confirm the nav links to `/sites`, `/nodes`, `/alerts`, `/settings` all exist (lines 47–67 of the current file). They do — no change needed.

- [ ] **Step 3: Type-check**

```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews"
pnpm --filter lews-web exec tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews"
git add "apps/web/app/(app)/sites/page.tsx" "apps/web/app/(app)/sites/[id]/page.tsx" "apps/web/app/(app)/nodes/page.tsx" "apps/web/app/(app)/nodes/[id]/page.tsx" "apps/web/app/(app)/alerts/page.tsx" "apps/web/app/(app)/settings/page.tsx"
git commit -m "feat(web): stub 6 non-hero pages with 'Coming soon' panel"
```

---

## Task 8: End-to-end browser verification

**Files:** none — verification only.

- [ ] **Step 1: Start the dev server**

```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews/apps/web"
pnpm dev
```

Expected: Next.js compiles, prints `✓ Ready in N ms`, listening on `http://localhost:3000`. **Zero compilation errors.**

- [ ] **Step 2: Open the dashboard**

Open `http://localhost:3000` in a browser. Open DevTools → Network tab.

Verify each row of this table (all must pass):

| # | Check | Pass |
|---|-------|------|
| 1 | Land on `/dashboard` (no `/login` redirect) | ☐ |
| 2 | DevTools Network tab shows **zero** requests to `localhost:8000` | ☐ |
| 3 | 4 KPI cards visible: Active Alerts (3), Critical Alerts (1), Online Nodes (13 / 15), 24h Rainfall (48 mm) | ☐ |
| 4 | Map preview on dashboard shows ~15 colored markers around Bandung (mix of green/yellow/orange/red) | ☐ |
| 5 | 3 alert cards visible: 1 red (Critical), 1 orange (Warning), 1 yellow (Watch) | ☐ |
| 6 | "Nodes (15)" grid shows exactly 15 cards, each with a status dot, severity badge, battery V, and sparkline | ☐ |
| 7 | Sidebar shows "Demo User · admin@lews.dev", Logout button is disabled | ☐ |
| 8 | DevTools console: zero errors, zero warnings | ☐ |

- [ ] **Step 3: Open the map page**

Click "Map" in the sidebar (or visit `http://localhost:3000/map`).

Verify:

| # | Check | Pass |
|---|-------|------|
| 9 | Full-screen Leaflet map with 15 severity-colored markers | ☐ |
| 10 | Legend in bottom-left shows all 4 severity levels with correct colors | ☐ |
| 11 | Click a marker → side panel slides in from the right showing node name, site, status, severity badge, battery, last seen, lat/lon, 24h rain sparkline | ☐ |
| 12 | "View full details" button is visibly disabled | ☐ |
| 13 | Click "← Close" → side panel disappears | ☐ |

- [ ] **Step 4: Test the stub routes**

Click each in the sidebar: Sites, Nodes, Alerts, Settings.

Verify:

| # | Check | Pass |
|---|-------|------|
| 14 | Each shows the "Coming soon" panel with 🚧 emoji, "Back to Dashboard" link | ☐ |
| 15 | Clicking "Back to Dashboard" returns to `/dashboard` | ☐ |

- [ ] **Step 5: Verify determinism**

Hard-refresh the browser (Ctrl+Shift+R) on `/dashboard`.

Verify:

| # | Check | Pass |
|---|-------|------|
| 16 | Same exact numbers, same marker positions, same alert titles, same node severities | ☐ |

- [ ] **Step 6: Verify responsive layout**

Resize the browser to 1280px and then 1920px wide.

Verify:

| # | Check | Pass |
|---|-------|------|
| 17 | At 1280px: KPI grid is 4 columns, alerts/map split is 50/50, no horizontal scroll | ☐ |
| 18 | At 1920px: same layout, no horizontal scroll, map fills available space | ☐ |

- [ ] **Step 7: Stop the dev server**

Press Ctrl+C in the terminal where `pnpm dev` is running.

- [ ] **Step 8: Final commit if any tweaks were needed**

If any verification step forced a code tweak, commit it:
```bash
cd "C:/Users/rakha/OneDrive/Documents/workspace/landslide-ews"
git add -u
git commit -m "fix(web): tweaks from end-to-end verification"
```

If everything passed first try, skip this step.

---

## Self-Review

**1. Spec coverage:**

| Spec section | Covered by |
|---|---|
| §1 fixtures (tenant, sites, nodes, alerts, KPI) | Task 2 |
| §2 API_URL export | Task 1 |
| §3 layout strip auth | Task 4 |
| §4 page.tsx (no change) | Verification in Task 8 |
| §5 dashboard rewrite | Task 5 |
| §6 map rewrite + SiteMap fix | Tasks 3 + 6 |
| §7 stub pages | Task 7 |
| §8 visual polish (colors, dark mode) | Imported from shared-types in Tasks 5/6 |
| Verification checklist (13 steps) | Task 8 |

No gaps.

**2. Placeholder scan:**
- No "TBD", "TODO", "implement later", "similar to Task N" in the plan body. (The "TODO" reference in Task 3 step 1 quotes the existing line in `SiteMap.tsx` — it's a comment from the source, not a placeholder in this plan.)
- Every step has concrete code or commands.
- Every file path is absolute and exact.
- No "add appropriate error handling" — fixtures are deterministic, no try/catch needed.

**3. Type consistency:**
- `nodeSeverities: Record<string, Severity>` defined in Task 2, used in Tasks 5 and 6 — consistent.
- `nodeSparklines: Record<string, number[]>` defined in Task 2, used in Tasks 5 and 6 — consistent.
- `getSiteById`, `getNodeById` exported in Task 2, used in Tasks 5 and 6 — consistent.
- `SiteMap` props `{ nodes, severities?, onMarkerClick? }` defined in Task 3, used in Tasks 5 and 6 — consistent.
- `kpi.rainfall_24h_mm`, `kpi.avg_battery_mv`, `kpi.online_nodes`, `kpi.total_nodes` — match the `KPISummary` interface in `packages/shared-types/src/index.ts` (verified during spec writing).
- `SEVERITY_COLORS[severity].bg/.text/.border` — matches the record shape in `packages/shared-types/src/enums.ts:37-42`.

No type drift.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-08-demo-dashboard.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
