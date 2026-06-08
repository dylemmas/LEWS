'use client';

import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Severity, batteryPercent, type NodeDTO } from '@lews/shared-types';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default marker icons in Next.js
// @ts-expect-error - adding getIconUrl to fix leaflet marker
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const SEVERITY_COLORS: Record<Severity, string> = {
  [Severity.Normal]: '#22c55e',     // green
  [Severity.Watch]: '#3b82f6',      // blue
  [Severity.Warning]: '#eab308',    // yellow
  [Severity.Critical]: '#ef4444',   // red
};

interface SiteMapProps {
  nodes: NodeDTO[];
  /** Per-node severity (same length and order as nodes), used to colour the markers. */
  severities?: Severity[];
  /** Optional: called when a marker is clicked. */
  onNodeClick?: (nodeId: string) => void;
  /** Optional: a node id to highlight (e.g. the one whose panel is open). */
  selectedNodeId?: string | null;
}

export default function SiteMap({ nodes, severities, onNodeClick, selectedNodeId }: SiteMapProps) {
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
      {nodes.map((node, i) => (
        <SeverityMarker
          key={node.id}
          node={node}
          severity={severities?.[i] ?? Severity.Normal}
          onClick={onNodeClick}
          selected={node.id === selectedNodeId}
        />
      ))}
    </MapContainer>
  );
}

function SeverityMarker({
  node,
  severity,
  onClick,
  selected,
}: {
  node: NodeDTO;
  severity: Severity;
  onClick?: (nodeId: string) => void;
  selected: boolean;
}) {
  const color = SEVERITY_COLORS[severity];
  const ringColor = selected ? '#0ea5e9' : 'white';
  const ringWidth = selected ? 4 : 3;

  const icon = L.divIcon({
    className: 'custom-div-icon',
    html: `<div style="
      background-color: ${color};
      width: 24px;
      height: 24px;
      border-radius: 50%;
      border: ${ringWidth}px solid ${ringColor};
      box-shadow: 0 2px 4px rgba(0,0,0,0.4);
      transition: border 120ms ease;
    "></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });

  return (
    <Marker
      position={[node.lat, node.lon]}
      icon={icon}
      eventHandlers={{
        click: () => onClick?.(node.id),
      }}
    >
      <Popup>
        <div className="min-w-[200px]">
          <h3 className="mb-1 font-semibold">{node.name || node.dev_eui}</h3>
          <p className="mb-1 text-sm text-slate-600">{node.dev_eui}</p>
          <p className="mb-1 text-sm">
            Status: <span className="capitalize">{node.status}</span>
          </p>
          {node.battery_mv && (
            <p className="mb-1 text-sm">
              Battery: {batteryPercent(node.battery_mv)}%
            </p>
          )}
        </div>
      </Popup>
    </Marker>
  );
}
