'use client';

import { NavLink } from './NavLink';
import { HOME_ICONS } from './nav-items';

export function Sidebar({ currentPath }: { currentPath: string }) {
  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
      <div className="p-4 border-b border-slate-800">
        <h1 className="text-xl font-bold text-white">Landslide EWS</h1>
        <p className="text-xs text-slate-400 mt-1">Early Warning Dashboard</p>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {HOME_ICONS.map((item) => (
          <NavLink
            key={item.href}
            href={item.href}
            icon={item.icon}
            label={item.label}
            active={currentPath === item.href}
          />
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <button
          onClick={() => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
          }}
          className="w-full text-left px-3 py-2 rounded-md text-sm text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
