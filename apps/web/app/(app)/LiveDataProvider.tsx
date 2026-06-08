'use client';

import { useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { connectWebSocket, disconnectWebSocket } from '@/lib/ws';

export function LiveDataProvider({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();

  useEffect(() => {
    if (status === 'authenticated' && session?.user) {
      const { accessToken, tenantId } = session.user as any;
      if (accessToken && tenantId) {
        connectWebSocket(accessToken, tenantId);
      }
    }
    return () => {
      disconnectWebSocket();
    };
  }, [session, status]);

  return <>{children}</>;
}
