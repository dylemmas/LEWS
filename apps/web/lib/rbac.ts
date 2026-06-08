import type { UserRole } from '@lews/shared-types';

const ROLE_RANK: Record<UserRole, number> = {
  admin: 3,
  operator: 2,
  viewer: 1,
};

export function can(userRole: UserRole | null, required: UserRole): boolean {
  if (!userRole) return false;
  return ROLE_RANK[userRole] >= ROLE_RANK[required];
}

export function canModifyAlerts(userRole: UserRole | null): boolean {
  return can(userRole, 'operator');
}

export function canManageSites(userRole: UserRole | null): boolean {
  return can(userRole, 'operator');
}

export function canInjectEvents(userRole: UserRole | null): boolean {
  return can(userRole, 'admin');
}
