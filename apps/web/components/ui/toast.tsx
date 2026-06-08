'use client';

import { useEffect, useState } from 'react';

let toastId = 0;
export function toast(msg: string) {
  const e = new CustomEvent<ToastMessage>('toast', { detail: { id: ++toastId, msg } });
  window.dispatchEvent(e);
}

type ToastMessage = { id: number; msg: string };

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [queue, setQueue] = useState<ToastMessage[]>([]);
  useEffect(() => {
    const h = (e: Event) => {
      const msg = (e as CustomEvent<ToastMessage>).detail;
      setQueue((q) => [...q, msg]);
      setTimeout(() => setQueue((q) => q.filter((m) => m.id !== msg.id)), 5000);
    };
    window.addEventListener('toast', h);
    return () => window.removeEventListener('toast', h);
  }, []);
  return (
    <>
      {children}
      {queue.length > 0 && (
        <div className="fixed right-3 top-3 z-50 flex flex-col gap-2">
          {queue.map((t) => (
            <div key={t.id} className="rounded bg-card border border-border px-3 py-2 text-sm shadow-lg">
              {t.msg}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
