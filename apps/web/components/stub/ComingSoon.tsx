import type { ReactNode } from 'react';

interface ComingSoonProps {
  title: string;
  description: string;
  bullets?: string[];
  children?: ReactNode;
}

export default function ComingSoon({
  title,
  description,
  bullets,
  children,
}: ComingSoonProps) {
  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-slate-800 bg-slate-900 px-6 py-4">
        <h1 className="text-xl font-bold text-white">{title}</h1>
        <p className="text-sm text-slate-400">{description}</p>
      </header>

      <div className="flex flex-1 items-center justify-center p-6">
        <div className="max-w-lg rounded border border-slate-800 bg-slate-900 p-6">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-amber-700/50 bg-amber-950/30 px-2.5 py-1 text-xs font-medium text-amber-300">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
            Coming soon
          </div>
          <h2 className="text-lg font-semibold text-white">
            Full functionality is part of the next milestone
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            This view is part of the production build that will run against the
            live FastAPI + TimescaleDB stack. For the presentation demo, the
            Dashboard and Map pages are fully populated with synthetic data.
          </p>

          {bullets && bullets.length > 0 && (
            <ul className="mt-4 space-y-1.5 text-sm text-slate-400">
              {bullets.map((b) => (
                <li key={b}>· {b}</li>
              ))}
            </ul>
          )}

          {children && <div className="mt-5">{children}</div>}

          <a
            href="/dashboard"
            className="mt-6 inline-block rounded border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition hover:bg-slate-700"
          >
            ← Back to dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
