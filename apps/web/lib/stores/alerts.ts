import { create } from 'zustand';
import type { AlertEvent } from '@lews/shared-types';

interface AlertsState {
  topAlerts: AlertEvent[];
  prependAlert: (alert: AlertEvent) => void;
  clearAlert: (alertId: string) => void;
  setAlerts: (alerts: AlertEvent[]) => void;
}

export const useAlertsStore = create<AlertsState>(set => ({
  topAlerts: [],
  prependAlert: alert =>
    set(state => ({
      topAlerts: [
        alert,
        ...state.topAlerts.filter(a => a.alert_id !== alert.alert_id),
      ].slice(0, 5),
    })),
  clearAlert: alertId =>
    set(state => ({
      topAlerts: state.topAlerts.filter(a => a.alert_id !== alertId),
    })),
  setAlerts: alerts => set({ topAlerts: alerts }),
}));
