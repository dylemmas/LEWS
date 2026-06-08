'use client';

import { useState } from 'react';

type Scenario = 'rain_burst' | 'tilt_spike' | 'crack_jump' | 'critical';

export default function InjectEventButton() {
  const [open, setOpen] = useState(false);
  const [scenario, setScenario] = useState<Scenario>('critical');
  const [loading, setLoading] = useState(false);

  const handleInject = async () => {
    setLoading(true);

    const token = localStorage.getItem('access_token');

    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/v1/ingest/sim/inject`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ scenario, duration_sec: 60 }),
        }
      );

      setOpen(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(!open)}
        className="rounded bg-purple-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-purple-700"
      >
        Inject Demo Event
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-lg border border-slate-800 bg-slate-900 p-6 shadow-xl">
            <h2 className="mb-4 text-lg font-semibold text-white">
              Inject Demo Scenario
            </h2>

            <div className="mb-4 space-y-3">
              {[
                { id: 'rain_burst', label: 'Rain Burst', desc: 'Heavy rainfall event' },
                { id: 'tilt_spike', label: 'Tilt Spike', desc: 'Sudden ground movement' },
                { id: 'crack_jump', label: 'Crack Jump', desc: 'Crack width increase' },
                { id: 'critical', label: 'Critical', desc: 'All sensors maxed' },
              ].map((opt) => (
                <label
                  key={opt.id}
                  className={`flex cursor-pointer rounded border p-3 transition ${
                    scenario === opt.id
                      ? 'border-purple-500 bg-purple-500/10'
                      : 'border-slate-800 bg-slate-900 hover:border-slate-700'
                  }`}
                >
                  <input
                    type="radio"
                    name="scenario"
                    value={opt.id}
                    checked={scenario === opt.id}
                    onChange={(e) => setScenario(e.target.value as Scenario)}
                    className="sr-only"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-white">{opt.label}</div>
                    <div className="text-sm text-slate-400">{opt.desc}</div>
                  </div>
                  {scenario === opt.id && (
                    <div className="text-purple-500">●</div>
                  )}
                </label>
              ))}
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setOpen(false)}
                disabled={loading}
                className="rounded border border-slate-700 px-4 py-2 text-sm font-medium text-slate-400 transition hover:border-slate-600 hover:text-white disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleInject}
                disabled={loading}
                className="rounded bg-purple-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-purple-700 disabled:opacity-50"
              >
                {loading ? 'Injecting...' : 'Inject'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
