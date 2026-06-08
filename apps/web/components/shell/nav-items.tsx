import { LayoutDashboard, Map, Activity, AlertTriangle, Settings } from 'lucide-react';

export const HOME_ICONS = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/map', label: 'Map', icon: Map },
  { href: '/nodes', label: 'Nodes', icon: Activity },
  { href: '/alerts', label: 'Alerts', icon: AlertTriangle },
  { href: '/settings', label: 'Settings', icon: Settings },
] as const;
