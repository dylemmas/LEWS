'use client';

import { useEffect, useMemo } from 'react';
import { io, type Socket } from 'socket.io-client';
import { useReadingsStore } from '@/lib/stores/readings';
import { useAlertsStore } from '@/lib/stores/alerts';
import { useNodesStore } from '@/lib/stores/nodes';
import type { ReadingEvent, AlertEvent, NodeStatusEvent } from '@lews/shared-types/ws';

export function LiveDataProvider({ children }: { children: React.ReactNode }) {
  const setReading = useReadingsStore((s) => s.set);
  const prependAlert = useAlertsStore((s) => s.prepend);
  const updateNodeStatus = useNodesStore((s) => s.updateStatus);

  const socket: Socket | null = useMemo(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return null;

    return io(`${process.env.NEXT_PUBLIC_API_URL}`, {
      path: '/v1/ws/stream',
      transports: ['websocket'],
      reconnection: true,
      auth: { token },
    });
  }, []);

  useEffect(() => {
    if (!socket) return;

    socket.on('connect', () => {
      console.log('WS connected');
    });

    socket.on('reading', (event: ReadingEvent) => {
      setReading(event.node_id, {
        time: event.time,
        severity: event.severity,
        rain_tips_15m: event.rain_tips_15m,
        accel_rms_mg: event.accel_rms_mg,
        tilt_delta_ddeg: event.tilt_delta_ddeg,
        crack_delta_mm10: event.crack_delta_mm10,
        battery_mv: event.battery_mv,
        ml_prob: event.ml_prob,
        lat: event.lat,
        lon: event.lon,
      });
    });

    socket.on('alert', (event: AlertEvent) => {
      prependAlert({
        id: event.alert_id,
        node_id: event.node_id,
        site_id: event.site_id,
        severity: event.severity,
        state: event.state,
        title: event.title,
        message: event.message,
        first_seen_at: event.first_seen_at,
        last_seen_at: event.last_seen_at,
        acknowledged_at: event.acknowledged_at,
        resolved_at: event.resolved_at,
        ml_prob: event.ml_prob,
      });
    });

    socket.on('node_status', (event: NodeStatusEvent) => {
      updateNodeStatus(event.node_id, {
        status: event.status,
        last_seen_at: event.last_seen_at,
        battery_mv: event.battery_mv,
      });
    });

    return () => {
      socket.disconnect();
    };
  }, [socket, setReading, prependAlert, updateNodeStatus]);

  return <>{children}</>;
}
