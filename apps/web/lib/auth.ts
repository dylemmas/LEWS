import type { AuthSession, UserDTO, UserRole } from '@lews/shared-types';

let authState: AuthSession | null = null;

export function setAuth(session: AuthSession) {
  authState = session;
  localStorage.setItem('access_token', session.access_token);
  localStorage.setItem('refresh_token', session.refresh_token);
  localStorage.setItem('user', JSON.stringify(session.user));
  localStorage.setItem('tenant', JSON.stringify(session.tenant));
}

export function getAuth(): AuthSession | null {
  if (!authState) {
    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');
    const tenantStr = localStorage.getItem('tenant');
    const refresh = localStorage.getItem('refresh_token');
    if (token && userStr && tenantStr && refresh) {
      authState = {
        access_token: token,
        refresh_token: refresh,
        token_type: 'bearer',
        expires_in: 900,
        user: JSON.parse(userStr) as UserDTO,
        tenant: JSON.parse(tenantStr),
      };
    }
  }
  return authState;
}

export function getCurrentUser(): UserDTO | null {
  return getAuth()?.user ?? null;
}

export function getCurrentTenantId(): string | null {
  return getAuth()?.tenant?.id ?? null;
}

export function getCurrentRole(): UserRole | null {
  return getAuth()?.user?.role ?? null;
}

export function clearAuth() {
  authState = null;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  localStorage.removeItem('tenant');
}

export function isAuthenticated(): boolean {
  return !!getAuth();
}
