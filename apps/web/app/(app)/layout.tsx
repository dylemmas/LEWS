'use client';

import { usePathname } from 'next/navigation';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/map', label: 'Map' },
  { href: '/alerts', label: 'Alerts' },
  { href: '/nodes', label: 'Nodes' },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex h-screen bg-slate-950">
      <aside className="flex w-64 flex-col border-r border-slate-800 bg-slate-900">
        <div className="flex h-16 items-center border-b border-slate-800 px-6">
          <h1 className="text-xl font-bold text-sky-400">LEWS</h1>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href;
            return (
              <a
                key={item.href}
                href={item.href}
                className={`block rounded px-3 py-2 text-sm font-medium transition ${
                  active
                    ? 'bg-sky-950 text-sky-400'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                }`}
              >
                {item.label}
              </a>
            );
          })}
        </nav>

        <div className="border-t border-slate-800 bg-slate-900 p-4">
          <div className="text-sm">
            <div className="font-medium text-slate-200">Demo User</div>
            <div className="text-xs text-slate-500">admin@acme.test</div>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
